import click
import cvxpy as cp
import numpy as np
import polars as pl
from tqdm import tqdm


def calculer_reports(t1_values, t2_values, solver="CLARABEL"):
    """Calcule la matrice de report

    :param t1_values: la matrice des votes de premier tour
    :param t2_values:  la matrice des votes de premier tour
    :return: la matrice de report

    t1_values et t2_values ont :
    - autant de lignes que de bureaux de vote dans la commune
    - autant de colonnes que de choix possibles au tour correspondant

    La dernière colonne correspond au nombre de personnes s'étant abstenu

    La matrice de report a autant de lignes que de choix de premier tour et autant de
    colonnes que de choix de second tour.
    """

    # pour prendre en compte les situations de radiation / ajout d'électeurs
    excedents = t1_values.sum(axis=1) - t2_values.sum(axis=1)

    N1 = t1_values.shape[1]
    N2 = t2_values.shape[1]

    t1_values = np.append(t1_values, np.maximum(-excedents, 0)[:, np.newaxis], axis=1)
    t2_values = np.append(t2_values, np.maximum(excedents, 0)[:, np.newaxis], axis=1)

    # La N2+1ème colonne se déduit de la valeur des autres, la somme de chaque ligne devant être 1
    matrice_report = cp.Variable(shape=(N1 + 1, N2), nonneg=True)
    constraints = [matrice_report.sum(axis=1) <= np.ones(N1 + 1)]

    matrice_report_complete = cp.hstack(
        [
            matrice_report,
            1 - matrice_report.sum(axis=1).reshape([N1 + 1, 1], order="C"),
        ]
    )

    prediction = t1_values @ matrice_report_complete

    objective = cp.Minimize(cp.sum_squares(prediction - t2_values))

    problem = cp.Problem(objective, constraints)

    problem.solve(solver=solver)

    if matrice_report.value is not None:
        return matrice_report.value[:-1, :]


def calculer_r_square(t1_values, t2_values, report):
    predicted_t2 = t1_values @ report
    var_totale = t2_values.var(axis=0)
    var_residuels = (t2_values - predicted_t2).var(axis=0)
    var_totale = np.maximum(var_totale, 1e-10)
    return 1 - var_residuels / var_totale


@click.command()
@click.option("--t1", type=click.Path(exists=True, dir_okay=False), required=True)
@click.option("--t2", type=click.Path(exists=True, dir_okay=False), required=True)
@click.option("--key", required=True)
@click.option(
    "-o", "--output", type=click.Path(writable=True, dir_okay=False), required=True
)
def main(t1, t2, key, output):
    resultats_t1 = pl.read_parquet(t1)
    resultats_t2 = pl.read_parquet(t2)

    resultats_t1 = resultats_t1.with_columns(
        bureau_de_vote=pl.format("{code_commune}-{bureau_de_vote}")
    )
    resultats_t2 = resultats_t2.with_columns(
        bureau_de_vote=pl.format("{code_commune}-{bureau_de_vote}")
    )

    unites = (
        resultats_t2.group_by(key)
        .agg(
            pl.col("numero_panneau").n_unique().alias("nb_listes_t2"),
            pl.col("bureau_de_vote").n_unique().alias("nb_bureaux"),
        )
        .join(
            resultats_t1.group_by(key).agg(
                pl.col("numero_panneau").n_unique().alias("nb_listes_t1"),
            ),
            on=key,
            validate="1:1",
        )
    )

    abstention_t1 = (
        resultats_t1.group_by("bureau_de_vote")
        .agg(
            pl.col(key).first(),
            pl.col("inscrits").first(),
            pl.col("voix").sum().alias("exprimés"),
        )
        .select(
            key,
            "bureau_de_vote",
            (pl.col("inscrits") - pl.col("exprimés")).alias("abstention"),
        )
    )

    abstention_t2 = (
        resultats_t2.group_by("bureau_de_vote")
        .agg(
            pl.col(key).first(),
            pl.col("inscrits").first(),
            pl.col("voix").sum().alias("exprimés"),
        )
        .select(
            key,
            "bureau_de_vote",
            (pl.col("inscrits") - pl.col("exprimés")).alias("abstention"),
        )
    )

    # on veut au moins autant de bureaux que de variables
    unites = unites.filter(
        pl.col("nb_listes_t1") * pl.col("nb_listes_t1") <= pl.col("nb_bureaux")
    )[key]

    report_par_unite = {}

    for unite in tqdm(unites):
        t2_unite = (
            resultats_t2.sort(["bureau_de_vote", "numero_panneau"])
            .filter(pl.col(key) == unite)
            .pivot(
                on=["numero_panneau"],
                index=["bureau_de_vote"],
                values=["voix"],
                maintain_order=True,
            )
            .join(
                abstention_t2.filter(pl.col(key) == unite).select(
                    "bureau_de_vote", "abstention"
                ),
                on=["bureau_de_vote"],
                validate="1:1",
                maintain_order="left",
            )
        )

        t1_unite = (
            resultats_t1.sort(["bureau_de_vote", "numero_panneau"])
            .filter(pl.col(key) == unite)
            .pivot(
                on=["numero_panneau"],
                index=["bureau_de_vote"],
                values=["voix"],
                maintain_order=True,
            )
            .join(
                abstention_t1.filter(pl.col(key) == unite).select(
                    "bureau_de_vote", "abstention"
                ),
                on=["bureau_de_vote"],
                validate="1:1",
                maintain_order="left",
            )
        )

        t2_values = t2_unite.select(pl.all().exclude(["bureau_de_vote"])).to_numpy()
        t1_values = t1_unite.select(pl.all().exclude(["bureau_de_vote"])).to_numpy()

        matrice_report = calculer_reports(t1_values, t2_values)

        if matrice_report is not None:
            r_square = calculer_r_square(t1_values, t2_values, matrice_report)

            report_par_unite[unite] = (matrice_report.flatten("C"), r_square)

    df_reports = pl.DataFrame(
        {
            key: report_par_unite.keys(),
            "coefficients": [c for c, _ in report_par_unite.values()],
            "r_square": [r for _, r in report_par_unite.values()],
        }
    )

    df_reports.write_parquet(output)


if __name__ == "__main__":
    main()
