import click
import polars as pl


@click.command()
@click.argument("in_path", type=click.Path(exists=True, dir_okay=False, readable=True))
@click.argument("out_path", type=click.Path(dir_okay=False, writable=True))
@click.option("--code")
@click.option("--communautaire", is_flag=True)
def clean(in_path, out_path, code, communautaire):
    candidats = pl.scan_csv(
        in_path,
        separator=";",
        schema_overrides={
            "Code circonscription": pl.String,
        },
    )

    colonnes = [
        pl.col("Code circonscription").alias(code),
        pl.col("Numéro de panneau").alias("numero_panneau"),
        pl.col("Libellé abrégé de liste").alias("liste_court"),
        pl.col("Libellé de la liste").alias("liste"),
        pl.col("Code nuance de liste").alias("nuance"),
        pl.col("Ordre").alias("ordre"),
        pl.col("Sexe").alias("sexe"),
        pl.col("Nom sur le bulletin de vote").alias("nom"),
        pl.col("Prénom sur le bulletin de vote").alias("prenom"),
        pl.col("Nationalité").alias("nationalite"),
        pl.col("Code personnalité").alias("code_personnalite"),
    ]

    if communautaire:
        colonnes.append(pl.col("CC").is_not_null().alias("candidat_communautaire"))

    candidats = candidats.select(*colonnes).filter(
        pl.col("numero_panneau").is_not_null()
    )

    candidats.sink_parquet(out_path)


if __name__ == "__main__":
    clean()
