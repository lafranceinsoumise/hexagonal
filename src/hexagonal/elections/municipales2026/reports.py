import click
import cvxpy as cp
import numpy as np
import polars as pl
from tqdm import tqdm


def calculer_reports(t1_values, t2_values, solver="CLARABEL"):
    """Calcule la matrice de report

    :param t1_values: le vecteur des votes de premier tour
    :param t2_values:  le vecteur des votes de premier tour
    :return: la matrice de report

    Les deux vecteurs t1_values et t2_values doivent contenir en dernière position le nombre de personnes
    s'étant abstenu.
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
    return 1 - var_residuels / var_totale


@click.group()
def main(): ...


@main.command()
@click.argument("resultats_t1", type=click.Path(exists=True, dir_okay=False))
@click.argument("resultats_t2", type=click.Path(exists=True, dir_okay=False))
@click.argument("reports", type=click.Path(writable=True, dir_okay=False))
def municipales(resultats_t1, resultats_t2, reports):
    resultats_t1 = pl.read_parquet(resultats_t1)
    resultats_t2 = pl.read_parquet(resultats_t2)

    communes = (
        resultats_t2.group_by("code_commune")
        .agg(
            pl.col("numero_panneau").n_unique().alias("nb_listes_t2"),
            pl.col("bureau_de_vote").n_unique().alias("nb_bureaux"),
        )
        .join(
            resultats_t1.group_by("code_commune").agg(
                pl.col("numero_panneau").n_unique().alias("nb_listes_t1"),
            ),
            on="code_commune",
            validate="1:1",
        )
    )

    abstention_t1 = (
        resultats_t1.group_by(["code_commune", "bureau_de_vote"])
        .agg(
            pl.col("inscrits").first(),
            pl.col("voix").sum().alias("exprimés"),
        )
        .select(
            "code_commune",
            "bureau_de_vote",
            (pl.col("inscrits") - pl.col("exprimés")).alias("abstention"),
        )
    )

    abstention_t2 = (
        resultats_t2.group_by(["code_commune", "bureau_de_vote"])
        .agg(pl.col("inscrits").first(), pl.col("voix").sum().alias("exprimés"))
        .select(
            "code_commune",
            "bureau_de_vote",
            (pl.col("inscrits") - pl.col("exprimés")).alias("abstention"),
        )
    )

    # on veut au moins autant de bureaux que de variables
    communes = communes.filter(
        pl.col("nb_listes_t1") * pl.col("nb_listes_t1") <= pl.col("nb_bureaux")
    )["code_commune"]

    report_par_commune = {}

    for code_commune in tqdm(communes):
        t2 = (
            resultats_t2.sort(["bureau_de_vote", "numero_panneau"])
            .filter(pl.col("code_commune") == code_commune)
            .pivot(
                on=["numero_panneau"],
                index=["bureau_de_vote"],
                values=["voix"],
                maintain_order=True,
            )
            .join(
                abstention_t2.filter(pl.col("code_commune") == code_commune).select(
                    "bureau_de_vote", "abstention"
                ),
                on=["bureau_de_vote"],
                validate="1:1",
                maintain_order="left",
            )
        )

        t1 = (
            resultats_t1.sort(["bureau_de_vote", "numero_panneau"])
            .filter(pl.col("code_commune") == code_commune)
            .pivot(
                on=["numero_panneau"],
                index=["bureau_de_vote"],
                values=["voix"],
                maintain_order=True,
            )
            .join(
                abstention_t1.filter(pl.col("code_commune") == code_commune).select(
                    "bureau_de_vote", "abstention"
                ),
                on=["bureau_de_vote"],
                validate="1:1",
                maintain_order="left",
            )
        )

        t2_values = t2.select(pl.all().exclude(["bureau_de_vote"])).to_numpy()
        t1_values = t1.select(pl.all().exclude(["bureau_de_vote"])).to_numpy()

        matrice_report = calculer_reports(t1_values, t2_values)

        if matrice_report is not None:
            r_square = calculer_r_square(t1_values, t2_values, matrice_report)

            report_par_commune[code_commune] = (matrice_report.flatten("C"), r_square)

    df_reports = pl.DataFrame(
        {
            "code_commune": report_par_commune.keys(),
            "coefficients": [c for c, _ in report_par_commune.values()],
            "r_square": [r for _, r in report_par_commune.values()],
        }
    )

    df_reports.write_parquet(reports)


if __name__ == "__main__":
    main()
