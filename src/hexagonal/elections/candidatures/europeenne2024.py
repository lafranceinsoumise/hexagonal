import click
import polars as pl


@click.command()
@click.argument("in_path", type=click.Path(exists=True, dir_okay=False, readable=True))
@click.argument("out_path", type=click.Path(dir_okay=False, writable=True))
def clean(in_path, out_path):
    candidats = pl.scan_csv(
        in_path,
        separator=";",
    )

    candidats = candidats.select(
        pl.col("Numéro de panneau").alias("numero_panneau"),
        pl.col("Libellé de la liste").alias("liste"),
        pl.col("Ordre").alias("ordre"),
        pl.col("Sexe").alias("sexe"),
        pl.col("Nom sur le bulletin de vote").alias("nom"),
        pl.col("Prénom sur le bulletin de vote").alias("prenom"),
        pl.col("Date de naissance").alias("date_naissance"),
        pl.col("Profession").alias("profession"),
        pl.col("Code personnalité").alias("code_personnalite"),
        pl.col("Sortant").is_not_null().alias("sortant"),
    ).filter(pl.col("numero_panneau").is_not_null())

    candidats.sink_parquet(out_path)


if __name__ == "__main__":
    clean()
