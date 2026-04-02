import sys

from hexagonal.files.spec import get_pandas_dataframe


def etablir_correspondances(resultats, candidats, destination):
    resultats = get_pandas_dataframe(
        resultats,
    )
    candidats = get_pandas_dataframe(
        candidats,
    )

    correspondance = resultats.merge(candidats)[
        ["code_commune", "bureau_de_vote", "circonscription"]
    ].drop_duplicates()

    assert (
        correspondance.duplicated(["code_commune", "bureau_de_vote"], keep=False).sum()
        == 0
    )

    correspondance.to_csv(destination, index=False)


def run():
    etablir_correspondances(*sys.argv[1:])


if __name__ == "__main__":
    run()
