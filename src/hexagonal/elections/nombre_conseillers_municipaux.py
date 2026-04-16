import click
import polars as pl

from hexagonal.files.spec import get_polars_dataframe

input_file = click.Path(exists=True, dir_okay=False, readable=True)
output_file = click.Path(dir_okay=False, writable=True)


# attention ce tableau doit être trié
ANNEES_SCRUTINS_MUNICIPAUX = [2014, 2020, 2026]

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


def cas_plm(plm_2026, plm_pre_2026, population):
    # Pour 2026, le nombre de conseillers PLM est fixé directement
    plm_2026 = pl.read_csv(
        plm_2026, schema_overrides={"code_commune": pl.String}
    ).select(
        pl.lit(2026, pl.Int64).alias("annee"),
        "code_commune",
        pl.col("nombre").alias("nombre_conseillers"),
    )

    plm_pre_2026 = (
        pl.read_csv(
            plm_pre_2026,
        )
        .with_columns(code_commune=pl.col("code_secteur").str.slice(0, 5))
        .group_by("annee", "code_commune")
        .agg(nombre_conseillers=pl.col("nombre").sum())
    ).sort("annee", "code_commune")

    plm_pre_2026 = (
        pl.DataFrame({"annee": [a for a in ANNEES_SCRUTINS_MUNICIPAUX if a < 2026]})
        .join(pl.DataFrame({"code_commune": ["13055", "69123", "75056"]}), how="cross")
        .join_asof(
            plm_pre_2026,
            by="code_commune",
            left_on="annee",
            right_on="annee",
            strategy="backward",
            check_sortedness=False,
        )
        .select("annee", "code_commune", "nombre_conseillers")
    )

    plm = pl.concat([plm_2026, plm_pre_2026])
    plm = plm.join(population, on=["annee", "code_commune"], how="left").select(
        "annee", "code_commune", "population", "nombre_conseillers"
    )

    return plm.sort(["annee", "code_commune"])


def recuperer_population_reference(population):
    pop_columns = {
        annee: f"population_municipale_{annee - 3}"
        for annee in ANNEES_SCRUTINS_MUNICIPAUX
    }

    population = get_polars_dataframe(
        population, columns=["code_commune", *pop_columns.values()]
    )

    population = pl.concat(
        population.select(
            pl.lit(annee, dtype=pl.Int64).alias("annee"),
            "code_commune",
            pl.col(c).alias("population"),
        )
        for annee, c in pop_columns.items()
    )

    # on traite le cas parisien : il faut sommer les populations par arrondissement
    population = (
        population.with_columns(
            code_commune=pl.when(pl.col("code_commune").str.starts_with("75"))
            .then(pl.lit("75056"))
            .otherwise(pl.col("code_commune"))
        )
        .group_by("annee", "code_commune")
        .agg(pl.col("population").sum().alias("population"))
    )

    # on écarte les communes sans population qui n'ont pas de conseil municipal
    population = population.filter(pl.col("population") > 0)

    return population


@click.command()
@click.option("--population", type=input_file, required=True)
@click.option("--nb-conseillers", type=input_file, required=True)
@click.option("--plm-2026", type=input_file, required=True)
@click.option("--plm-pre-2026", type=input_file, required=True)
@click.option("--output", type=output_file, required=True)
def main(population, nb_conseillers, plm_2026, plm_pre_2026, output):
    population = recuperer_population_reference(population)
    nb_conseillers = pl.read_csv(nb_conseillers)

    cas_general = (
        population.sort("population")
        .join_asof(
            nb_conseillers,
            left_on="population",
            right_on="seuil_population",
            strategy="backward",
            check_sortedness=True,
        )
        .select("annee", "code_commune", "population", "nombre_conseillers")
    )

    plm = cas_plm(plm_2026, plm_pre_2026, population)

    resultat = (
        pl.concat([cas_general, plm])
        .unique(["annee", "code_commune"], keep="last")
        .sort(["annee", "code_commune"])
    )

    # pour les villes de moins de 9000 habitants, on utilise le nombre de grands
    # électeurs prévus par le code électoral article L284
    nb_grands_electeurs_m9000 = pl.DataFrame(
        {
            "nombre_conseillers": NB_GRANDS_ELECTEURS_M9000.keys(),
            "nombre_grands_electeurs": NB_GRANDS_ELECTEURS_M9000.values(),
        }
    )

    # Pour les villes de plus de 9000 habitants, tous les conseillers municipaux sont
    # grands électeurs. Par ailleurs, pour les villes de plus de 30 000 habitants,
    # des délégués supplémentaires sont attribués par tranche de 800 habitants
    # au-delà de 30 000.
    nb_grands_electeurs_p9000 = (
        pl.col("nombre_conseillers")
        + pl.max_horizontal(pl.lit(0), pl.col("population") - 30000) // 800
    )

    resultat = resultat.join(
        nb_grands_electeurs_m9000, on="nombre_conseillers", how="left"
    ).with_columns(
        nombre_grands_electeurs=pl.when(pl.col("population") < 9000)
        .then(pl.col("nombre_grands_electeurs"))
        .otherwise(nb_grands_electeurs_p9000)
    )

    resultat.write_parquet(output)


if __name__ == "__main__":
    main()
