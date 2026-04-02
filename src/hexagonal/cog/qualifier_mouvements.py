from collections import deque

import click
import pandas as pd

from hexagonal.files.spec import get_pandas_dataframe

EVENEMENTS_FUSION = [
    "fusion association",
    "création commune nouvelle",
    "fusion simple",
    "création",
]
ANNULATION_FUSION = "rétablissement"


def calculer_correspondances(chemin_mvt, date_limite):
    mvt = get_pandas_dataframe(chemin_mvt)

    # on se limite aux mouvements survenus après la date limite
    mvt = mvt[mvt["date_effet"] >= date_limite]

    # pour chaque fusion, on récupère une ligne ancienne commune -> commune nouvelle
    fusions = mvt[
        mvt["type_evenement"].isin(EVENEMENTS_FUSION)
        & (mvt["type_commune_avant"] == "COM")
        & (mvt["type_commune_apres"] == "COM")
        & (mvt["code_commune_avant"] != mvt["code_commune_apres"])
    ].copy()
    # pour associer plus facilement les annulations, il vaut mieux échanger les codes
    # avant et codes après
    annulations_fusions = mvt.assign(
        code_commune_avant=mvt["code_commune_apres"],
        code_commune_apres=mvt["code_commune_avant"],
    ).loc[
        (mvt["type_evenement"] == ANNULATION_FUSION)
        & (mvt["type_commune_avant"] == "COM")
        & (mvt["type_commune_apres"] == "COM")
        & (mvt["code_commune_avant"] != mvt["code_commune_apres"]),
        ["code_commune_avant", "code_commune_apres", "date_effet"],
    ]

    annulations_fusions = fusions.reset_index().merge(
        annulations_fusions.reset_index(),
        how="inner",
        on=["code_commune_avant", "code_commune_apres"],
        suffixes=("", "_annulation"),
    )
    # l'annulation survient toujours après la fusion
    # On garde la première annulation après la fusion, s'il y en a plusieurs
    # mais ce cas n'existe pas encore avec le COG 2024.
    annulations_fusions = (
        annulations_fusions[
            annulations_fusions["date_effet"]
            < annulations_fusions["date_effet_annulation"]
        ]
        .sort_values("date_effet_annulation")
        .drop_duplicates(["index_annulation"], keep="first")
    )

    # on ne garde que les fusions non annulées
    fusions = fusions[~fusions.index.isin(annulations_fusions["index"])]

    autres_changements = mvt[
        ~mvt["type_evenement"].isin(EVENEMENTS_FUSION)
        & (mvt["type_evenement"] != ANNULATION_FUSION)
        & (mvt["type_commune_avant"] == "COM")
        & (mvt["type_commune_apres"] == "COM")
        & (mvt["code_commune_avant"] != mvt["code_commune_apres"])
    ].copy()

    autres_changements["clé"] = autres_changements.apply(
        lambda r: tuple(sorted([r["code_commune_avant"], r["code_commune_apres"]])),
        axis=1,
    )
    autres_changements = autres_changements.sort_values("date_effet").drop_duplicates(
        "clé", keep="last"
    )

    tous_changements = pd.concat(
        [
            fusions[["code_commune_avant", "code_commune_apres"]],
            autres_changements[["code_commune_avant", "code_commune_apres"]],
        ]
    ).drop_duplicates()
    assert tous_changements["code_commune_avant"].is_unique

    correspondances = {}

    codes_initiaux = set(tous_changements["code_commune_avant"])
    pairs = deque(
        zip(
            tous_changements["code_commune_avant"],
            tous_changements["code_commune_apres"],
            strict=False,
        ),
        maxlen=len(tous_changements),
    )
    while pairs:
        pair = pairs.popleft()
        if pair[1] in codes_initiaux and pair[1] not in correspondances:
            pairs.append(pair)
        else:
            correspondances[pair[0]] = correspondances.get(pair[1], pair[1])

    correspondances = pd.DataFrame(
        {
            "code_commune_avant": correspondances.keys(),
            "code_commune_apres": correspondances.values(),
        }
    )

    return correspondances


@click.command()
@click.argument(
    "chemin_mouvements", type=click.Path(exists=True, dir_okay=False, readable=True)
)
@click.argument("date", type=click.DateTime())
@click.argument("dest", type=click.Path(dir_okay=False, writable=True))
def run(chemin_mouvements, date, dest):
    correspondances = calculer_correspondances(chemin_mouvements, date)

    correspondances.to_csv(dest, index=False)


if __name__ == "__main__":
    run()
