import sys

import polars as pl

from hexagonal.files.spec import get_polars_dataframe


def etablir_correspondances(resultats, candidats, destination):
    resultats = get_polars_dataframe(
        resultats,
    )
    candidats = get_polars_dataframe(
        candidats,
    )

    correspondance = (
        resultats.join(
            candidats,
            on=["numero_panneau", "nom", "prenom", "sexe"],
        )
        .select("code_commune", "bureau_de_vote", "circonscription")
        .unique()
        .sort(["code_commune", "bureau_de_vote"])
    )

    assert (
        len(
            correspondance.filter(
                pl.struct("code_commune", "bureau_de_vote").is_duplicated()
            )
        )
        == 0
    )

    correspondance.write_csv(destination)


def run():
    etablir_correspondances(*sys.argv[1:])


if __name__ == "__main__":
    run()
