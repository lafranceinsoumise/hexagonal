import click
import polars as pl


@click.command()
@click.argument("in_path", type=click.Path(exists=True, dir_okay=False, readable=True))
@click.argument("out_path", type=click.Path(dir_okay=False, writable=True))
def clean(in_path, out_path):
    candidats = pl.read_csv(
        in_path,
        separator="\t",
        encoding="latin-1",
        schema_overrides={
            "Code de la région": pl.String,
            "Code section électorale": pl.String,
        },
    )

    candidats = candidats.select(
        pl.col("Code de la région").alias("code_region"),
        pl.col("Code section électorale").alias("code_section_electorale"),
        pl.col("N° Panneau Liste").alias("numero_panneau"),
        pl.col("Code Dépôt Liste").alias("code_depot"),
        pl.col("Libellé Etendu Liste").alias("liste"),
        pl.col("Nuance Liste").alias("nuance"),
        pl.col("N° candidat").alias("ordre"),
        pl.col("Sexe candidat").alias("sexe"),
        pl.col("Nom candidat").alias("nom"),
        pl.col("Prénom candidat").alias("prenom"),
        pl.col("Nom nais. candidat").alias("nom_naissance"),
        pl.col("Prénom nais. candidat").alias("prenom_naissance"),
        pl.col("Date naissance candidat").alias("date_naissance"),
        pl.col("Profession candidat").alias("profession"),
    ).filter(pl.col("numero_panneau").is_not_null())

    candidats.write_parquet(out_path)


if __name__ == "__main__":
    clean()
