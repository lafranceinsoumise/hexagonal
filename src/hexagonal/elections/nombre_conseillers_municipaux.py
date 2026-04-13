from functools import reduce

import click
import polars as pl

from hexagonal.files.spec import get_polars_dataframe

input_file = click.Path(exists=True, dir_okay=False, readable=True)
output_file = click.Path(dir_okay=False, writable=True)


ANNEES_SCRUTINS_MUNICIPAUX = [2026, 2020, 2014]

# code électoral L284
NB_GRANDS_ELECTEURS_M9000 = {
    7: 1,
    11: 1,
    15: 3,
    19: 5,
    23: 7,
    27: 15,
    29: 15,
}


@click.command()
@click.option("--population", type=input_file)
@click.option("--nb-conseillers", type=input_file)
@click.option("--output", type=output_file)
def main(population, nb_conseillers, output):
    population = get_polars_dataframe(population)
    nb_conseillers = pl.read_csv(nb_conseillers)

    # on écarte les communes sans population qui n'ont pas de conseil municipal
    population = population.filter(pl.col("population_municipale_2023") > 0)

    # on écarte les cas de Paris, Lyon et Marseille qui sont spécifiques
    population = population.filter(
        ~pl.col("code_commune").str.starts_with("75")
        & ~pl.col("code_commune").is_in(["13055", "69123"])
    )

    par_annee = []
    for annee in ANNEES_SCRUTINS_MUNICIPAUX:
        population_reference = population.select(
            "code_commune",
            pl.col(f"population_municipale_{annee - 3}").alias("population"),
        ).sort("population")

        par_annee.append(
            population_reference.join_asof(
                nb_conseillers,
                left_on="population",
                right_on="seuil_population",
                strategy="backward",
                check_sortedness=True,
            ).select(
                pl.lit(annee).alias("annee"),
                "code_commune",
                "population",
                "nombre_conseillers",
            )
        )

    resultat = pl.concat(par_annee).sort(["annee", "code_commune"])

    nb_grands_electeurs_m9000 = reduce(
        lambda c, nb: c.when(pl.col("nombre_conseillers") == nb[0]).then(pl.lit(nb[1])),
        NB_GRANDS_ELECTEURS_M9000.items(),
        pl,
    )
    nb_grands_electeurs_p9000 = (
        pl.col("nombre_conseillers")
        + pl.max_horizontal(pl.lit(0), pl.col("population") - 30000) // 800
    )

    resultat = resultat.with_columns(
        nombre_grands_electeurs=pl.when(pl.col("population") < 9000)
        .then(nb_grands_electeurs_m9000)
        .otherwise(nb_grands_electeurs_p9000)
    )

    resultat.write_parquet(output)


if __name__ == "__main__":
    main()
