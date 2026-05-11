import click
import polars as pl

from hexagonal.files.spec import get_polars_dataframe
from hexagonal.utils.polars import normaliser


@click.command()
@click.argument("parrainages_path", type=click.Path(exists=True, dir_okay=False))
@click.argument("elus_municipaux_path", type=click.Path(exists=True, dir_okay=False))
@click.argument("output_path", type=click.Path(writable=True, dir_okay=False))
def main(parrainages_path: str, elus_municipaux_path: str, output_path: str):
    parrainages = (
        get_polars_dataframe(parrainages_path)
        .filter(pl.col("mandat").is_in(["maire", "maire délégué"]))
        .select(
            pl.col("code_circonscription").alias("code_commune"),
            normaliser("nom").alias("nom_normalise"),
            normaliser("prenom").alias("prenom_normalise"),
            "candidat",
        )
    )

    maires = (
        get_polars_dataframe(elus_municipaux_path)
        .filter(pl.col("fonction").is_in(["Maire", "Maire délégué"]))
        .select(
            "code_commune",
            "nom",
            "prenom",
            "fonction",
            nom_normalise=normaliser("nom"),
            prenom_normalise=normaliser("prenom"),
        )
    )

    parrains_en_poste = parrainages.join(
        maires, on=["code_commune", "nom_normalise", "prenom_normalise"]
    )

    parrains_en_poste.write_csv(output_path)


if __name__ == "__main__":
    main()
