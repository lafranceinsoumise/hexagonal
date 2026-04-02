from pathlib import Path

import click

from hexagonal.cog.types import TypeCommune
from hexagonal.files.spec import get_pandas_dataframe


def qualifier_codes_postaux(codes_postaux, communes):
    codes_postaux = codes_postaux[["code_postal", "code_commune"]].drop_duplicates()
    communes = communes[communes["type_commune"] == TypeCommune.COMMUNE]

    codes_postaux = codes_postaux.merge(
        communes[["code_commune", "nom", "population_municipale"]],
        on="code_commune",
    )

    par_code_postal = (
        codes_postaux.sort_values(["code_postal", "population_municipale"])
        .drop_duplicates("code_postal", keep="last")
        .set_index("code_postal")
        .rename(
            columns={
                "code_commune": "code_commune_principale",
                "nom": "nom_commune_principale",
                "population_municipale": "population_commune_principale",
            }
        )
    )

    par_code_postal["autres_communes"] = (
        codes_postaux.sort_values(
            ["code_postal", "population_municipale"], ascending=[True, False]
        )
        .groupby("code_postal")["nom"]
        .agg(lambda g: ", ".join(g.iloc[1:]))
    )

    par_code_postal["population_totale"] = codes_postaux.groupby("code_postal")[
        "population_municipale"
    ].sum()

    return par_code_postal


@click.command()
@click.argument(
    "codes_postaux_path",
    type=click.Path(exists=True, readable=True, file_okay=True, dir_okay=False),
)
@click.argument(
    "communes_path",
    type=click.Path(exists=True, readable=True, path_type=Path),
)
@click.argument("dest_path", type=click.Path(writable=True, dir_okay=False))
def run(codes_postaux_path, communes_path, dest_path):
    codes_postaux = get_pandas_dataframe(codes_postaux_path)
    communes = get_pandas_dataframe(communes_path)
    codes_postaux_qualifies = qualifier_codes_postaux(codes_postaux, communes)

    codes_postaux_qualifies.to_csv(dest_path)


if __name__ == "__main__":
    run()
