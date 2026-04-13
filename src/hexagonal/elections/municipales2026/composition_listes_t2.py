from functools import partial, reduce

import click
import polars as pl

from hexagonal.trigram_search import TrigramIndex


def traitement_cas_special(cond, correction, *, colonne_code):
    (code, numero, ordre), valeur = correction

    return cond.when(
        (pl.col(colonne_code) == code)
        & (pl.col("numero_panneau") == numero)
        & (pl.col("ordre") == ordre)
    ).then(pl.lit(valeur))


def correction_numero_panneau(cas, code: str):
    corrections = [(c[:3], c[3]) for c in cas]
    return (
        reduce(partial(traitement_cas_special, colonne_code=code), corrections, pl)
        .otherwise(pl.col("numero_panneau_t1"))
        .alias("numero_panneau_t1")
    )


def correction_ordre(cas, code: str):
    corrections = [(c[:3], c[4]) for c in cas]
    return (
        reduce(partial(traitement_cas_special, colonne_code=code), corrections, pl)
        .otherwise(pl.col("ordre_t1"))
        .alias("ordre_t1")
    )


def normaliser(colonne):
    if isinstance(colonne, str):
        colonne = pl.col(colonne)
    return (
        colonne.str.normalize("NFKD")
        .str.to_lowercase()
        .str.replace_all(r"\p{Nonspacing Mark}", "")  # diacritiques
        .str.replace_all(r"\pP", " ")  # ponctuation
        .str.replace_all(r"[^a-z0-9 ]+", "")
        .str.replace_all(r"\s\s+", " ")
        .str.strip_chars()
    )


def trouver_correspondances(candidatures_t1, candidatures_t2, code: str):
    champs_normalises = {"nom_n": normaliser("nom"), "prenom_n": normaliser("prenom")}

    candidatures_t1 = candidatures_t1.with_columns(**champs_normalises).with_row_index()
    candidatures_t2 = candidatures_t2.with_columns(**champs_normalises).with_row_index()

    jointure_exacte = candidatures_t2.join(
        candidatures_t1,
        on=[code, "sexe", "nom_n", "prenom_n"],
        how="left",
        suffix="_t1",
    )

    # la deuxième condition permet d'éliminer les cas d'homonymie nom + prénom
    candidatures_correspondent = (
        pl.col("index_t1").is_not_null()
        & ~pl.struct(code, "numero_panneau", "ordre").is_duplicated()
    )

    jointure_simple = jointure_exacte.filter(candidatures_correspondent)

    circonscriptions_anomalies = jointure_exacte.filter(~candidatures_correspondent)[
        code
    ].unique()

    cle_comparaison = normaliser(
        pl.col("prenom")
        + " "
        + pl.col("nom")
        + " "
        + pl.col("nuance").fill_null("NA")
        + " "
        + pl.col("numero_panneau").cast(pl.String)
    ).alias("clé")

    candidatures_t1_restantes = candidatures_t1.filter(
        ~pl.col("index").is_in(jointure_simple["index_t1"].implode())
    ).with_columns(cle_comparaison)

    candidatures_t2_restantes = candidatures_t2.filter(
        ~pl.col("index").is_in(jointure_simple["index"].implode())
    ).with_columns(cle_comparaison)

    jointure_fuzzy = []

    for circonscription in circonscriptions_anomalies:
        cs_t2 = candidatures_t2_restantes.filter(pl.col(code) == circonscription)
        cs_t1 = candidatures_t1_restantes.filter(pl.col(code) == circonscription)

        index_circo = TrigramIndex(cs_t1.select("clé", "index").iter_rows())

        matches = [index_circo.search(cle)[0][1] for cle in cs_t2["clé"]]

        jointure_fuzzy.append(
            pl.DataFrame({"index_t2": cs_t2["index"], "index_t1": matches})
        )

    jointure_fuzzy = (
        pl.concat(jointure_fuzzy)
        .join(
            candidatures_t2,
            left_on=["index_t2"],
            right_on=["index"],
        )
        .join(candidatures_t1, left_on=["index_t1"], right_on=["index"], suffix="_t1")
    )

    return pl.concat(
        [
            jointure_simple.filter(pl.col("numero_panneau_t1").is_not_null()).select(
                code,
                "numero_panneau",
                "ordre",
                "numero_panneau_t1",
                "ordre_t1",
            ),
            jointure_fuzzy.select(
                code,
                "numero_panneau",
                "ordre",
                "numero_panneau_t1",
                "ordre_t1",
            ),
        ]
    ).sort([code, "numero_panneau", "ordre"])


@click.command()
@click.argument(
    "candidatures_t1", type=click.Path(exists=True, readable=True, dir_okay=False)
)
@click.argument(
    "candidatures_t2", type=click.Path(exists=True, readable=True, dir_okay=False)
)
@click.argument(
    "resultats_t1", type=click.Path(exists=True, readable=True, dir_okay=False)
)
@click.argument("composition", type=click.Path(writable=True, dir_okay=False))
@click.argument(
    "composition_nominative", type=click.Path(writable=True, dir_okay=False)
)
@click.option(
    "--code",
)
def main(
    candidatures_t1,
    candidatures_t2,
    resultats_t1,
    composition,
    composition_nominative,
    code,
):
    candidatures_t1 = pl.read_parquet(candidatures_t1)
    candidatures_t2 = pl.read_parquet(candidatures_t2)
    resultats_t1 = (
        pl.read_parquet(resultats_t1)
        .cast({code: pl.String})
        .group_by([code, "numero_panneau"])
        .agg(
            pl.col("voix").sum(),
        )
        .with_columns(part=pl.col("voix") / pl.col("voix").sum().over(code))
    )

    candidatures_t1 = candidatures_t1.join(
        resultats_t1,
        on=[code, "numero_panneau"],
        how="left",
    )

    assert candidatures_t1["part"].is_not_null().all()

    # On ne garde que les listes qui ont fait plus de 5 % au premier tour
    candidatures_t1 = candidatures_t1.filter(pl.col("part") >= 0.05)

    correspondances = trouver_correspondances(
        candidatures_t1, candidatures_t2, code=code
    )

    speciaux = [
        # deux Fatima ALI avec le même nom dans la même liste à Tsingoni
        ("97617", 5, 10, 5, 4),
        ("97617", 5, 20, 5, 20),
        # deux Isabelle LEFEBVRE, dans deux listes qui fusionnent ensemble
        ("59009", 5, 13, 3, 6),
    ]

    correspondances = correspondances.with_columns(
        correction_numero_panneau(speciaux, code=code),
        correction_ordre(speciaux, code=code),
    )

    correspondances.write_parquet(composition_nominative)

    comp = correspondances.group_by([code, "numero_panneau", "numero_panneau_t1"]).agg(
        pl.col("ordre").count().alias("nombre")
    )

    comp.join(
        candidatures_t2.filter(pl.col("ordre") == 1).select(
            code, "numero_panneau", "liste", "nuance"
        ),
        on=[code, "numero_panneau"],
    ).join(
        candidatures_t1.filter(pl.col("ordre") == 1).select(
            code, "numero_panneau", "liste", "nuance"
        ),
        left_on=[code, "numero_panneau_t1"],
        right_on=[code, "numero_panneau"],
        suffix="_t1",
    ).sort(
        [
            code,
            "numero_panneau",
            "numero_panneau_t1",
        ]
    ).select(
        code,
        "numero_panneau",
        "liste",
        "nuance",
        "numero_panneau_t1",
        "liste_t1",
        "nuance_t1",
        "nombre",
    ).write_parquet(composition)


if __name__ == "__main__":
    main()
