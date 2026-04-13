"""Ce fichier comprend la routine permettant de nettoyer les fichiers électoraux des
scrutins post 2017

Le format employé après 2017 est un CSV à nombre de champs variable (sauf pour les
scrutins nationaux où les candidatures sont partout les mêmes).

Il y a une ligne par bureau de vote avec un certain nombre de champs fixes donnant
les informations propres au bureau de vote (identifiants INSEE, nombre d'inscrits,
nombre de bulletins exprimés, etc.) et ensuite les champs correspondant aux
informations d'un candidat sont répétées autant de fois que nécessaire.

Le format est toujours à peu près le même, mais les entêtes utilisés semblent changer
quasiment à chaque scrutin… Les deux tables de correspondance normalisent les noms de
champs."""

import csv
import sys

import pandas as pd

from hexagonal.codes import (
    normaliser_code_circonscription,
    normaliser_code_commune,
    normaliser_code_departement,
)

# convertit les codes départements utilisés par le ministère de l'intérieur avant 2024
correspondance_departements = {
    "ZA": "971",
    "ZB": "972",
    "ZC": "973",
    "ZD": "974",
    "ZM": "976",
    "ZN": "988",
    "ZP": "987",
    "ZS": "975",
    "ZW": "986",
}

# la variété des noms d'entête utilisés donne le tournis
fixed_headers = {
    "Code localisation": None,
    "Libellé localisation": None,
    "Code du département": "departement",
    "Code département": "departement",
    "Libellé du département": None,
    "Libellé département": None,
    "Libellé de la section électorale": None,
    "Code de la circonscription": "numero_circonscription",
    "Code circonscription législative": "circonscription",
    "Libellé de la circonscription": None,
    "Libellé circonscription législative": None,
    "Code du canton": "canton",
    "Libellé du canton": None,
    "Code de la commune": "commune",
    "Code commune": "code_commune",
    "Libellé de la commune": None,
    "Libellé commune": None,
    "Code secteur": "code_secteur",
    "Libellé secteur": None,
    "Code du b.vote": "bureau_de_vote",
    "Code B.Vote": "bureau_de_vote",
    "Code BV": "bureau_de_vote",
    "Inscrits": "inscrits",
    "Abstentions": None,
    "% Abs/Ins": None,
    "% Abstentions": None,
    "Votants": "votants",
    "% Vot/Ins": None,
    "% Votants": None,
    "Blancs": "blancs",
    "% Blancs/Ins": None,
    "% Blancs/inscrits": None,
    "% Blancs/Vot": None,
    "% Blancs/votants": None,
    "Nuls": None,
    "% Nuls/Ins": None,
    "% Nuls/inscrits": None,
    "% Nuls/Vot": None,
    "% Nuls/votants": None,
    "Exprimés": "exprimes",
    "% Exp/Ins": None,
    "% Exp/Vot": None,
    "% Exprimés/inscrits": None,
    "% Exprimés/votants": None,
    "Etat saisie": None,
}
"""
Comment renommer les entêtes ?
"""

repeated_headers = {
    "N°Panneau": "numero_panneau",
    "N.Pan.": "numero_panneau",
    "N°Liste": "numero_panneau",
    "Numéro de panneau": "numero_panneau",
    "Binôme": "binome",
    "Sexe": "sexe",
    "Sexe candidat": "sexe",
    "Nom": "nom",
    "Nom candidat": "nom",
    "Prénom": "prenom",
    "Prénom candidat": "prenom",
    "Nuance": "nuance",
    "Code Nuance": "nuance",
    "Nuance Liste": "nuance",
    "Nuance liste": "nuance",
    "Nuance candidat": "nuance",
    "Libellé Abrégé Liste": "liste_court",
    "Libellé abrégé de liste": "liste_court",
    "Libellé Etendu Liste": "liste_long",
    "Libellé de liste": "liste_long",
    "Liste": "liste_long",
    "Nom Tête de Liste": "tete_liste",
    "Voix": "voix",
    "% Voix/inscrits": None,
    "% Voix/exprimés": None,
    "% Voix/Ins": None,
    "% Voix/Exp": None,
    "Sièges / Elu": None,
    "Sièges Secteur": None,
    "Sièges CC": None,
    "Sièges au CC": None,
    "Sièges au CM": None,
    "Sièges": None,
    "Elu": None,
}


champs_entiers = [
    "inscrits",
    "votants",
    "exprimes",
    "blancs",
    "voix",
    "numero_panneau",
    "numero_liste",
]

champs_nuls_si_vide = ["nuance"]

identifiants = ["code_commune", "code_secteur", "bureau_de_vote", "circonscription"]
population = ["inscrits", "votants", "exprimes"]
par_candidat = [
    "numero_panneau",
    "nuance",
    "nom",
    "prenom",
    "sexe",
    "liste_court",
    "liste_long",
    "voix",
]

MAPPING_SEXE = {
    "M": "M",
    "F": "F",
    "MASCULIN": "M",
    "FEMININ": "F",
}


def read_file(src, delimiter=";", encoding="utf-8"):
    with open(src, "r", encoding=encoding, newline="") as in_file:
        r = csv.reader(in_file, delimiter=delimiter)

        headers = next(r)
        headers = [h.rstrip(" 0123456789") for h in headers]

        common_fields = [h for h in headers if h in fixed_headers]

        # attention aux répétitions
        candidate_specific_fields = []
        for h in headers:
            if h in repeated_headers and h not in candidate_specific_fields:
                candidate_specific_fields.append(h)

        unknown_fields = set(headers).difference(
            common_fields + candidate_specific_fields
        )
        if unknown_fields:
            raise ValueError(f"Champs inconnus : {', '.join(unknown_fields)}")

        fields = [
            fixed_headers[field]
            for field in common_fields
            if fixed_headers.get(field) is not None
        ] + [
            repeated_headers[field]
            for field in candidate_specific_fields
            if repeated_headers.get(field) is not None
        ]

        common_indices = [
            i for i, f in enumerate(common_fields) if fixed_headers[f] is not None
        ]
        candidate_specific_indices = [
            i
            for i, f in enumerate(candidate_specific_fields)
            if repeated_headers[f] is not None
        ]

        all_entries = []

        for line in r:
            common_values = [line[i] for i in common_indices]
            for candidate_offset in range(
                len(common_fields), len(line), len(candidate_specific_fields)
            ):
                candidate_specific_values = [
                    line[candidate_offset + j] for j in candidate_specific_indices
                ]
                if candidate_specific_values[-1] == "":
                    break
                all_entries.append(common_values + candidate_specific_values)

    resultats = pd.DataFrame(all_entries, columns=fields)

    for field in champs_entiers:
        if field in resultats.columns:
            try:
                resultats[field] = pd.to_numeric(
                    resultats[field],
                    errors="coerce",
                    dtype_backend="numpy_nullable",
                    downcast="unsigned",
                )
            except ValueError as e:
                print(f"global_fields: {common_fields!r}")
                print(f"repeated_fields: {candidate_specific_fields!r}")
                raise ValueError(f"Echec transformation entiers sur {field}") from e

    for field in champs_nuls_si_vide:
        if field in resultats.columns:
            resultats[field] = resultats[field].replace("", None)

    return resultats


def clean_results(src, dest, delimiter=";", encoding="utf-8"):
    resultats = read_file(src, delimiter, encoding=encoding)

    if "sexe" in resultats.columns:
        resultats["sexe"] = resultats["sexe"].map(MAPPING_SEXE)

    if "circonscription" in resultats.columns:
        resultats["circonscription"] = normaliser_code_circonscription(
            resultats["circonscription"]
        ).astype("category")
    if "numero_circonscription" in resultats.columns:
        departement = normaliser_code_departement(resultats["departement"])
        resultats["circonscription"] = (
            departement + "-" + resultats["numero_circonscription"].str.zfill(2)
        ).astype("category")

    if "commune" in resultats.columns:
        resultats["code_commune"] = resultats["departement"].str.zfill(2) + resultats[
            "commune"
        ].str.zfill(3)

    if "code_commune" in resultats.columns:
        resultats["code_commune"] = normaliser_code_commune(resultats["code_commune"])

    ids = [c for c in identifiants if c in resultats.columns]

    clean_columns = [
        c for c in (ids + population + par_candidat) if c in resultats.columns
    ]
    resultats = resultats.loc[:, clean_columns]
    resultats.to_parquet(dest, index=False)


def run():
    src, dest, encoding, delimiter = sys.argv[1:]
    clean_results(src, dest, delimiter=delimiter, encoding=encoding)


if __name__ == "__main__":
    run()
