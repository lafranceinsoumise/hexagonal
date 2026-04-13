import operator

import click
import polars as pl

ELUS_MUNICIPALES = {
    "elu_cm": ("ordre", "elus_cm"),
    "elu_cc": ("ordre_cc", "elus_cc"),
}

ELUS_CONSEILS_PLM = {
    "elu": ("ordre", "elus_conseil"),
}


def filtrer_elus(
    *,
    sieges_t1,
    sieges_t2,
    candidats_t1,
    candidats_t2,
    composition_nominative,
    code,
    champs_elus,
):

    listes_t1 = candidats_t1.unique([code, "numero_panneau"]).select(
        code,
        pl.col("numero_panneau", "liste", "nuance").name.suffix("_t1"),
    )

    est_elu = pl.fold(
        pl.lit(False),
        operator.or_,
        [pl.col(ordre) <= pl.col(elus) for ordre, elus in champs_elus.values()],
    )

    colonnes_elu = [
        (pl.col(ordre) <= pl.col(elus)).fill_null(False).alias(champ)
        for champ, (ordre, elus) in champs_elus.items()
    ]

    candidats_t1 = (
        candidats_t1.join(
            sieges_t1,
            on=[code, "numero_panneau"],
            validate="m:1",
        )
        .filter(est_elu)
        .select(
            code,
            "nom",
            "prenom",
            "sexe",
            *colonnes_elu,
            pl.col("numero_panneau", "liste", "nuance", "ordre").name.suffix("_t1"),
        )
    )

    candidats_t2 = (
        candidats_t2.join(
            sieges_t2,
            on=[code, "numero_panneau"],
            validate="m:1",
        )
        .filter(est_elu)
        .join(
            composition_nominative,
            on=[code, "numero_panneau", "ordre"],
            validate="1:1",
        )
        .join(
            listes_t1,
            on=[code, "numero_panneau_t1"],
            validate="m:1",
        )
        .select(
            code,
            "nom",
            "prenom",
            "sexe",
            *colonnes_elu,
            "numero_panneau_t1",
            "liste_t1",
            "nuance_t1",
            "ordre_t1",
            pl.col("numero_panneau", "liste", "nuance", "ordre").name.suffix("_t2"),
        )
    )

    return pl.concat([candidats_t2, candidats_t1], how="diagonal").sort(
        [code, "numero_panneau_t1", "ordre_t1"]
    )


@click.group()
def main(): ...


@main.command()
@click.argument("sieges_t1", type=click.Path(readable=True, dir_okay=False))
@click.argument("sieges_t2", type=click.Path(readable=True, dir_okay=False))
@click.argument("candidats_t1", type=click.Path(readable=True, dir_okay=False))
@click.argument("candidats_t2", type=click.Path(readable=True, dir_okay=False))
@click.argument(
    "composition_nominative", type=click.Path(readable=True, dir_okay=False)
)
@click.argument("elus", type=click.Path(writable=True, dir_okay=False))
def conseils_plm(
    sieges_t1, sieges_t2, candidats_t1, candidats_t2, composition_nominative, elus
):
    sieges_t1 = pl.read_parquet(
        sieges_t1, columns=["code_secteur", "numero_panneau", "elus_conseil"]
    )
    sieges_t2 = pl.read_parquet(
        sieges_t2, columns=["code_secteur", "numero_panneau", "elus_conseil"]
    )
    candidats_t1 = pl.read_parquet(candidats_t1)
    candidats_t2 = pl.read_parquet(candidats_t2)

    composition_nominative = pl.read_parquet(composition_nominative)

    candidats = filtrer_elus(
        sieges_t1=sieges_t1,
        sieges_t2=sieges_t2,
        candidats_t1=candidats_t1,
        candidats_t2=candidats_t2,
        composition_nominative=composition_nominative,
        code="code_secteur",
        champs_elus=ELUS_CONSEILS_PLM,
    )

    candidats.select(pl.all().exclude("elu")).write_parquet(elus)


@main.command()
@click.argument("sieges_t1", type=click.Path(readable=True, dir_okay=False))
@click.argument("sieges_t2", type=click.Path(readable=True, dir_okay=False))
@click.argument("candidats_t1", type=click.Path(readable=True, dir_okay=False))
@click.argument("candidats_t2", type=click.Path(readable=True, dir_okay=False))
@click.argument(
    "composition_nominative", type=click.Path(readable=True, dir_okay=False)
)
@click.argument("elus", type=click.Path(writable=True, dir_okay=False))
def municipales(
    sieges_t1, sieges_t2, candidats_t1, candidats_t2, composition_nominative, elus
):
    sieges_t1 = pl.read_parquet(
        sieges_t1, columns=["code_commune", "numero_panneau", "elus_cm", "elus_cc"]
    )
    sieges_t2 = pl.read_parquet(
        sieges_t2, columns=["code_commune", "numero_panneau", "elus_cm", "elus_cc"]
    )
    candidats_t1 = pl.read_parquet(candidats_t1).with_columns(
        ordre_cc=pl.when(pl.col("candidat_communautaire")).then(
            pl.col("ordre")
            .rank(method="ordinal")
            .over(["code_commune", "numero_panneau", "candidat_communautaire"])
        )
    )
    candidats_t2 = pl.read_parquet(candidats_t2).with_columns(
        ordre_cc=pl.when(pl.col("candidat_communautaire")).then(
            pl.col("ordre")
            .rank(method="ordinal")
            .over(["code_commune", "numero_panneau", "candidat_communautaire"])
        )
    )
    composition_nominative = pl.read_parquet(composition_nominative)

    candidats = filtrer_elus(
        sieges_t1=sieges_t1,
        sieges_t2=sieges_t2,
        candidats_t1=candidats_t1,
        candidats_t2=candidats_t2,
        composition_nominative=composition_nominative,
        code="code_commune",
        champs_elus=ELUS_MUNICIPALES,
    )

    candidats.write_parquet(elus)


if __name__ == "__main__":
    main()
