from typing import Iterable

import numpy as np

__all__ = [
    "proportionnelle_dhondt",
    "proportionnelle_reste_quotient_hare",
    "proportionnelle_reste_quotient_droop",
]

from numpy.typing import ArrayLike


def proportionnelle_dhondt(parts: ArrayLike, nb_sieges: int):
    """Méthode d'Hondt de répartition des sièges entre listes électorales

    :param parts: séquence des parts ou voix portées sur les différentes listes
    :param nb_sieges: nombre de sièges à répartir
    :return: séquence du nombre de sièges pour chaque liste, même ordre qu'en entrée
    """

    cutoffs = np.arange(nb_sieges) + 1.0
    return repartition_plus_forte_moyenne(parts, cutoffs)


def proportionnelle_sainte_lague(parts: ArrayLike, nb_sieges: int):
    cutoffs = np.arange(nb_sieges) + 0.5
    return repartition_plus_forte_moyenne(parts, cutoffs)


def proportionnelle_reste_quotient_hare(parts: ArrayLike, nb_sieges: int):
    quotient = sum(parts) / nb_sieges

    return repartition_plus_fort_reste(parts, nb_sieges, quotient)


def proportionnelle_reste_quotient_droop(parts: ArrayLike, nb_sieges: int):
    quotient = sum(parts) / (nb_sieges + 1)

    return repartition_plus_fort_reste(parts, nb_sieges, quotient)


def repartition_plus_forte_moyenne(parts: ArrayLike, seuils: ArrayLike):
    """Plus forte moyenne en utilisant les seuils en arguments

    :param parts: les parts (ou nombre de voix) reçues par les différentes listes
    :param seuils: les seuils utilisés pour la méthode de la plus forte moyenne
    :return: le nombre de sièges par liste, dans le même ordre qu'en entrée
    """
    parts = np.asarray(parts)
    seuils = np.asarray(seuils)
    quotients = parts[:, np.newaxis] / seuils
    selection = np.argsort(-quotients, axis=None)[: len(seuils)] // len(seuils)
    listes = np.arange(0, len(parts))

    return (listes[:, np.newaxis] == selection).sum(axis=1, dtype=np.int32)


def repartition_plus_fort_reste(
    parts: ArrayLike, nb_sieges: int, quotient: int | float
):
    parts = np.asarray(parts)
    nb = (parts // quotient).astype(np.int32)
    sieges_restants = int(nb_sieges - nb.sum())
    assert 0 <= sieges_restants <= nb_sieges
    reste = parts % quotient
    selection = np.argsort(-reste)[:sieges_restants]
    attribution_supplementaire = np.arange(0, len(parts))[:, np.newaxis] == selection
    siege_supplementaire = attribution_supplementaire.sum(axis=1, dtype=np.int32)

    return nb + siege_supplementaire
