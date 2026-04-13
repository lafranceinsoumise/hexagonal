import sys

import pandas as pd


def extraire_candidats(
    candidats, sensibilite_nfp, nuances_lfi24, nuances_lfi25, destination
):
    candidats = pd.read_csv(candidats)
    candidats["sortant"] = candidats["sortant"] == "OUI"
    candidats["sortant_suppleant"] = candidats["sortant_suppleant"] == "OUI"
    candidats["profession"] = candidats["profession"].str.slice(1, 3)

    sensibilite_nfp = pd.read_csv(sensibilite_nfp)[
        ["circonscription", "numero_panneau", "sensibilite"]
    ]
    nuances_lfi24 = pd.read_csv(nuances_lfi24)[
        ["circonscription", "numero_panneau", "nuance_lfi"]
    ]
    nuances_lfi25 = pd.read_csv(nuances_lfi25)[
        ["circonscription", "numero_panneau", "alliance", "parti"]
    ]

    candidats = candidats.merge(nuances_lfi24, how="left")
    candidats = candidats.merge(sensibilite_nfp, how="left")
    candidats = candidats.merge(nuances_lfi25, how="left")

    candidats.to_csv(destination, index=False)


def run():
    extraire_candidats(*sys.argv[1:])


if __name__ == "__main__":
    run()
