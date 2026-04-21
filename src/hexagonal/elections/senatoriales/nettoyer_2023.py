import logging

import click
import polars as pl
from dvc_objects.fs.utils import exists

from hexagonal.elections.senatoriales.types import TypeElectionSenatoriale
from hexagonal.utils.polars import polars_large_to_long

COLONNES_FIXES_MAJ_T1_ET_PROP: dict[str, pl.DataType | None] = {
    "code_localisation": None,
    "libelle_localisation": None,
    "code_departement": pl.String(),
    "nom_departement": None,
    "code_commune": None,
    "nom_commune": None,
    "code_bv": None,
    "inscrits": pl.Int32(),
    "votants": pl.Int32(),
    "part_votants": None,
    "abstentions": pl.Int32(),
    "part_abstentions": None,
    "exprimes": pl.Int32(),
    "part_exprimes": None,
    "part_exprimes_votants": None,
    "blancs": pl.Int32(),
    "part_blancs": None,
    "part_blancs_votants": None,
    "nuls": pl.Int32(),
    "part_nuls": None,
    "part_nuls_votants": None,
}

COLONNES_VARIABLES_MAJ_T1 = {
    "nuance": pl.String(),
    "nom": pl.String(),
    "prenom": pl.String(),
    "sexe": pl.String(),
    "nuance_liste": None,
    "libelle_liste_court": None,
    "libelle_liste": None,
    "voix": pl.Int32(),
    "part_voix_inscrits": None,
    "part_voix_exprimes": None,
    "elus": pl.String(),
    "sieges": None,
}

COLONNES_FIXES_MAJ_T2: dict[str, pl.DataType | None] = {
    "code_localisation": None,
    "libelle_localisation": None,
    "code_departement": pl.String(),
    "nom_departement": None,
    "code_commune": None,
    "nom_commune": None,
    "inscrits": pl.Int32(),
    "votants": pl.Int32(),
    "part_votants": None,
    "abstentions": pl.Int32(),
    "part_abstentions": None,
    "exprimes": pl.Int32(),
    "part_exprimes": None,
    "part_exprimes_votants": None,
    "blancs": pl.Int32(),
    "part_blancs": None,
    "part_blancs_votants": None,
    "nuls": pl.Int32(),
    "part_nuls": None,
    "part_nuls_votants": None,
}

COLONNES_VARIABLES_MAJ_T2 = {
    "nuance": pl.String(),
    "nom": pl.String(),
    "prenom": pl.String(),
    "sexe": pl.String(),
    "voix": pl.Int32(),
    "part_voix_inscrits": None,
    "part_voix_exprimes": None,
    "elus": pl.String(),
}


COLONNES_VARIABLES_PROP = {
    "nuance_vide": None,
    "nom_vide": None,
    "prenom_vide": None,
    "sexe_vide": None,
    "nuance": pl.String(),
    "libelle_liste_court": pl.String(),
    "libelle_liste": pl.String(),
    "voix": pl.Int32(),
    "part_voix_inscrits": None,
    "part_voix_exprimes": None,
    "elu_vide": None,
    "elus": pl.Int16(),
}


ORDRE_FINAL = [
    "code_departement",
    "type_scrutin",
    "inscrits",
    "votants",
    "abstentions",
    "exprimes",
    "blancs",
    "nuls",
    "nuance",
    "libelle_liste",
    "libelle_liste_court",
    "nom",
    "prenom",
    "sexe",
    "voix",
    "elus",
]


@click.command()
@click.argument("fichier", type=click.Path(exists=True, readable=True))
@click.argument("candidats", type=click.Path(exists=True, dir_okay=False))
@click.argument("resultats", type=click.Path(writable=True, dir_okay=False))
def main(fichier, candidats, resultats):
    logging.getLogger("fastexcel.types.dtype").setLevel(logging.ERROR)

    maj_t1 = pl.read_excel(
        fichier,
        sheet_name="MAJ - T1",
        read_options={"header_row": None, "skip_rows": 1},
    )
    maj_t1 = polars_large_to_long(
        maj_t1, COLONNES_FIXES_MAJ_T1_ET_PROP, COLONNES_VARIABLES_MAJ_T1
    )

    maj_t1 = maj_t1.with_columns(
        type_scrutin=pl.lit("MAJORITAIRE_T1", dtype=TypeElectionSenatoriale),
        elus=(pl.col("elus") == "élu").cast(pl.Int16()).fill_null(0),
    )

    maj_t2 = pl.read_excel(
        fichier,
        sheet_name="MAJ - T2",
        read_options={"header_row": None, "skip_rows": 1},
    )
    maj_t2 = polars_large_to_long(
        maj_t2, COLONNES_FIXES_MAJ_T2, COLONNES_VARIABLES_MAJ_T2
    )

    maj_t2 = maj_t2.with_columns(
        type_scrutin=pl.lit("MAJORITAIRE_T2", dtype=TypeElectionSenatoriale),
        elus=(pl.col("elus") == "élu").cast(pl.Int16()).fill_null(0),
    )

    prop = pl.read_excel(
        fichier,
        sheet_name="PROP",
        read_options={"header_row": None, "skip_rows": 1},
    )
    prop = polars_large_to_long(
        prop,
        COLONNES_FIXES_MAJ_T1_ET_PROP,
        COLONNES_VARIABLES_PROP,
    )
    prop = prop.with_columns(
        type_scrutin=pl.lit("PROPORTIONNELLE", dtype=TypeElectionSenatoriale)
    )

    candidats_prop = pl.read_excel(
        candidats,
        sheet_name="Scrutin proportionnel",
        schema_overrides={"Code département": pl.String()},
    )
    candidats_prop = candidats_prop.filter(pl.col("Ordre dans la liste") == 1).select(
        code_departement="Code département",
        libelle_liste="Libellé de la liste",
        nom="Nom candidat",
        prenom="Prénom candidat",
        sexe="Sexe candidat",
    )

    prop = prop.join(
        candidats_prop, on=["code_departement", "libelle_liste"], how="left"
    )

    res = (
        pl.concat([maj_t1, maj_t2, prop], how="diagonal")
        .sort(
            ["code_departement", "type_scrutin"],
        )
        .select(ORDRE_FINAL)
    )

    res.write_parquet(resultats)


if __name__ == "__main__":
    main()
