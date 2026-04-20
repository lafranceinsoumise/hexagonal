from dataclasses import dataclass

import pandas as pd


@dataclass
class Outremer:
    code_insee: str
    code_interieur: str
    nom: str


outremers = [
    Outremer("971", "ZA", "Guadeloupe"),
    Outremer("972", "ZB", "Martinique"),
    Outremer("973", "ZC", "Guyane"),
    Outremer("974", "ZD", "La Réunion"),
    Outremer("976", "ZM", "Mayotte"),
    Outremer("988", "ZN", "Nouvelle-Calédonie"),
    Outremer("987", "ZP", "Polynésie française"),
    Outremer("975", "ZS", "Saint-Pierre-et-Miquelon"),
    Outremer("986", "ZW", "Wallis-et-Futuna"),
    Outremer("977", "ZY", "Saint-Barthélemy"),
    Outremer("978", "ZT", "Saint-Martin"),
]

CORRESPONDANCE_CODE_DEPARTEMENT = {o.code_interieur: o.code_insee for o in outremers}
CORRESPONDANCE_CODE_DEPARTEMENT["99"] = "ZZ"


def normaliser_code_departement(departement: pd.Series) -> pd.Series:
    """Normalise une série de codes de département.

    Hexagonal reprend la convention du ministère de l'Intérieur utilisée en 2024 pour la
    codification des départements :
    - les départements de métropole ont un numéro de département sur 2 chiffres (avec un
      zéro initial pour les départements numérotés de 1 à 9)
    - les deux départements corses ont pour codes respectifs 2A et 2B
    - les départements et collectivités d'outre-mer ont un numéro à 3 chiffres
      commençant par 97 (départements d'Outremer et la collectivité d'Outremer de
      Saint-Pierre-et-Miquelon) ou par 98 (collectivités d'Outremer de Polynésie
      française, de Nouvelle-Calédonie et de Wallis-et-Futuna)
    - Saint-Barthélémy et Saint-Martin reçoivent un code département commun de ZX
    - ZZ pour les français de l'étranger (plutôt que le 99 employé par l'INSEE, car
      les codes « communes » utilisés par le ministère de l'Intérieur ne correspondent
      pas aux codes pays étrangers du COG)


    Jusqu'en 2024, le ministère de l'Intérieur n'utilisait pas les codes à trois
    chiffres de l'INSEE (par exemple 971 pour la Guadeloupe, 987 pour la Polynésie
    française, etc.) mais un code sur deux lettres (ZA pour la Guadeloupe, ZP pour la
    Polynésie française, etc.) Cela pose un problème particulier pour
    Saint-Barthélémy et Saint-Martin pour lesquels le code département ZX est
    utilisé, ce qui ne permet pas de les différencier à partir du seul numéro de
    département.

    À partir de 2024, le ministère de l'intérieur utilise bien les codes à 3 chiffres.

    :param departement: la série pandas de codes département à normaliser
    :return: une série pandas de codes département normalisés
    """
    return departement.map(CORRESPONDANCE_CODE_DEPARTEMENT).fillna(
        departement.str.zfill(2)
    )


def normaliser_code_circonscription(circonscription: pd.Series) -> pd.Series:
    """Normalise une série de codes de circonscription législative.

    hexagonal reprend la convention du ministère de l'Intérieur de 2024 pour la
    codification des départements, mais ajoute un tiret simple entre le numéro de
    département et le numéro de circonscription sur deux chiffres.

    La convention pour les départements est donc celle décrite en documentation de
    `normaliser_code_departement`.

    :param departement: la série pandas de codes circonscription à normaliser
    :return: une série pandas de codes circonscription normalisés
    """
    departement = normaliser_code_departement(circonscription.str.slice(0, -2))
    departement = departement.where(~departement.isin(["977", "978"]), "ZX")
    numero = circonscription.str.slice(-2)
    return departement.str.cat(numero, sep="-")


def normaliser_code_commune(commune: pd.Series) -> pd.Series:
    """Normalise une série de codes de commune.

    hexagonal suit la codification du COG comme décrit dans la documentation.

    Cette fonction traite notamment le cas des communes des départements et
    collectivités d'outre-mer pour lesquelles le code utilisé par le ministère de
    l'intérieur n'a pas toujours suivi la codification de l'INSEE, et comporte même
    des erreurs étranges.

    :param commune: la série pandas de codes commune à normaliser
    :return: une série pandas de codes commune normalisés
    """
    # identification du département
    commune = commune.str.zfill(5)
    partie_departement = commune.str.slice(0, 2)

    # on identifie les cas d'outremer hors Saint-Barthélémy
    codes_outremers_fe = (
        (partie_departement.map(CORRESPONDANCE_CODE_DEPARTEMENT) + commune.str.slice(3))
        .where(partie_departement != "ZX", "97" + commune.str.slice(2))
        .where(partie_departement != "99", "ZZ" + commune.str.slice(2))
    )

    return codes_outremers_fe.fillna(commune)
