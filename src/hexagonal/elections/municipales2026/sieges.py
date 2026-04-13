import click
import polars as pl

COLS = {
    "numero_panneau": "Numéro de panneau",
    "nuance": "Nuance liste",
    "liste_court": "Libellé abrégé de liste",
    "liste": "Libellé de liste",
}

COLS_MUNICIPALES = {
    **COLS,
    "elus_cm": "Sièges au CM",
    "elus_cc": "Sièges au CC",
}

COLS_CONSEILS_PLM = {
    **COLS,
    "elus_conseil": "Sièges",
}


def agreger(resultats, colonne_code, colonnes):
    n_max = int(resultats.columns[-1].split()[-1])

    selections = [
        {
            key: f"{value} {i}"
            for key, value in colonnes.items()
            if f"{value} 1" in resultats.columns
        }
        for i in range(1, n_max + 1)
    ]

    return (
        pl.concat([resultats.select(colonne_code, **s) for s in selections])
        .filter(pl.col("numero_panneau").is_not_null())
        .sort([colonne_code, "numero_panneau"])
    )


@click.group
def main():
    pass


@main.command()
@click.argument("resultats", type=click.Path(exists=True, dir_okay=False))
@click.argument("sieges", type=click.Path(writable=True, dir_okay=False))
def conseils_plm(resultats, sieges):
    resultats = pl.read_csv(
        resultats,
        separator=";",
        schema_overrides={
            "Code secteur": pl.String,
            "Code département": pl.String,
            **{f"Numéro de panneau {i}": pl.Int64 for i in range(1, 14)},
            **{f"Sièges {i}": pl.Int64 for i in range(1, 12)},
        },
    ).select(
        pl.col("Code secteur").alias("code_secteur"),
        pl.all().exclude("Code secteur"),
    )

    res = agreger(resultats, "code_secteur", COLS_CONSEILS_PLM).filter(
        pl.col("elus_conseil") != 0
    )

    res.write_parquet(sieges)


@main.command()
@click.argument("resultats", type=click.Path(exists=True, dir_okay=False))
@click.argument("sieges", type=click.Path(writable=True, dir_okay=False))
def municipales(resultats, sieges):
    resultats = pl.read_csv(
        resultats,
        separator=";",
        schema_overrides={
            "Code commune": pl.String,
            "Code département": pl.String,
            **{f"Numéro de panneau {i}": pl.Int64 for i in range(1, 14)},
            **{f"Sièges au CM {i}": pl.Int64 for i in range(1, 14)},
            **{f"Sièges au CC {i}": pl.Int64 for i in range(1, 14)},
        },
    ).select(
        pl.col("Code commune").alias("code_commune"),
        pl.all().exclude("Code commune"),
    )

    res = (
        agreger(resultats, "code_commune", COLS_MUNICIPALES)
        .filter(pl.col("elus_cm") != 0)
        .with_columns(pl.col("elus_cm").fill_null(0))
    )

    res.write_parquet(sieges)


if __name__ == "__main__":
    main()
