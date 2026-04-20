import numpy as np

__all__ = [
    "proportionnelle_dhondt",
    "proportionnelle_reste_quotient_hare",
    "proportionnelle_reste_quotient_droop",
]

from numpy.typing import ArrayLike, NDArray


def proportionnelle_dhondt(
    parts: NDArray[np.int_] | NDArray[np.floating],
    nb_sieges: int,
):
    """Méthode d'Hondt de répartition des sièges entre listes électorales

    :param parts: séquence des parts ou voix portées sur les différentes listes
    :param nb_sieges: nombre de sièges à répartir
    :return: séquence du nombre de sièges pour chaque liste, même ordre qu'en entrée
    """

    cutoffs = np.arange(nb_sieges) + 1.0
    return repartition_plus_forte_moyenne(parts, cutoffs)


def proportionnelle_sainte_lague(
    parts: NDArray[np.int_] | NDArray[np.floating],
    nb_sieges: int,
):
    cutoffs = np.arange(nb_sieges) + 0.5
    return repartition_plus_forte_moyenne(parts, cutoffs)


def proportionnelle_reste_quotient_hare(
    parts: NDArray[np.int_] | NDArray[np.floating],
    nb_sieges: int,
):
    quotient = parts.sum() / nb_sieges

    return repartition_plus_fort_reste(parts, nb_sieges, quotient)


def proportionnelle_reste_quotient_droop(
    parts: NDArray[np.int_] | NDArray[np.floating],
    nb_sieges: int,
):
    quotient = sum(parts) / (nb_sieges + 1)

    return repartition_plus_fort_reste(parts, nb_sieges, quotient)


def repartition_plus_forte_moyenne(
    parts: NDArray[np.int_] | NDArray[np.floating],
    seuils: NDArray[np.int_] | NDArray[np.floating],
):
    """Plus forte moyenne en utilisant les seuils en arguments

    :param parts: les parts (ou nombre de voix) reçues par les différentes listes
    :param seuils: les seuils utilisés pour la méthode de la plus forte moyenne
    :return: le nombre de sièges par liste, dans le même ordre qu'en entrée
    """
    nb_listes = len(parts)
    nb_sieges = len(seuils)

    # quotients est une matrice nb_liste * nb_sieges comprenant tous les quotients
    # possibles
    quotients = parts[:, np.newaxis] / seuils

    # on récupère les n_sieges plus grands quotients, qui correspondent aux sièges qui
    # seront attribués.
    selection = np.argsort(-quotients, axis=None)[:nb_sieges] // nb_sieges
    listes = np.arange(0, nb_listes)

    return (listes[:, np.newaxis] == selection).sum(axis=1, dtype=np.int32)


def repartition_plus_fort_reste(
    parts: NDArray[np.int_] | NDArray[np.floating],
    nb_sieges: int,
    quotient: int | float,
):
    nb = (parts // quotient).astype(np.int32)
    sieges_restants = int(nb_sieges - nb.sum())
    assert 0 <= sieges_restants <= nb_sieges
    reste = parts % quotient
    selection = np.argsort(-reste)[:sieges_restants]
    attribution_supplementaire = np.arange(0, len(parts))[:, np.newaxis] == selection
    siege_supplementaire = attribution_supplementaire.sum(axis=1, dtype=np.int32)

    return nb + siege_supplementaire
