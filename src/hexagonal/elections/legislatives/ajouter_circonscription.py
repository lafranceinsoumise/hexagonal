import click
import polars as pl

from hexagonal.files.spec import get_polars_dataframe


@click.command()
@click.option(
    "--resultats", type=click.Path(exists=True, dir_okay=False), required=True
)
@click.option(
    "--correspondance", type=click.Path(exists=True, dir_okay=False), required=True
)
@click.option("--output", type=click.Path(writable=True, dir_okay=False), required=True)
def ajouter_circonscription(resultats, correspondance, output):
    resultats = get_polars_dataframe(resultats)
    correspondance = get_polars_dataframe(correspondance)
    resultats = resultats.join(
        correspondance, on=["code_commune", "bureau_de_vote"]
    ).select(
        "code_commune",
        "bureau_de_vote",
        "circonscription",
        pl.all().exclude("code_commune", "bureau_de_vote", "circonscription"),
    )

    resultats.write_parquet(output)


if __name__ == "__main__":
    ajouter_circonscription()
