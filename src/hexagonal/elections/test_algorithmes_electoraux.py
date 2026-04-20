from .algorithmes_electoraux import (
    proportionnelle_dhondt,
    proportionnelle_reste_quotient_droop,
    proportionnelle_reste_quotient_hare,
    proportionnelle_sainte_lague,
)


def test_dhondt_wikipedia():
    # cas récupéré sur https://en.wikipedia.org/wiki/D%27Hondt_method
    voix = np.array(
        [
            100_000,
            80_000,
            30_000,
            20_000,
        ]
    )

    sieges = [4, 3, 1, 0]

    assert list(proportionnelle_dhondt(voix, sum(sieges))) == sieges


def test_dhondt_europeennes_2024():
    # les résultats aux européennes 2024

    # seules les listes qui ont dépassé les 5 % sont comptées
    voix = [
        7_765_936,  # Rassemblement national
        3_614_646,  # Ensemble/Renaissance
        3_424_216,  # PS/PP
        2_448_703,  # LFI
        1_794_171,  # LR
        1_361_883,  # Les Verts
        1_353_127,  # Reconquête
    ]

    sieges = [30, 13, 13, 9, 6, 5, 5]

    assert list(proportionnelle_dhondt(voix, sum(sieges))) == sieges


def test_sainte_lague_wikipedia():
    # https://en.wikipedia.org/wiki/Sainte-Lagu%C3%AB_method

    voix = [100_000, 80_000, 30_000, 20_000]
    sieges = [3, 3, 1, 1]

    assert list(proportionnelle_sainte_lague(voix, sum(sieges))) == sieges


def test_quotient_hare():
    voix = [1500, 1500, 900, 500, 500, 200]
    sieges = [7, 7, 4, 3, 3, 1]

    assert list(proportionnelle_reste_quotient_hare(voix, sum(sieges))) == sieges


def test_quotient_hare():
    voix = [47_000, 16_000, 15_800, 12_000, 6_100, 3_100]
    sieges = [5, 2, 2, 1, 0, 0]

    assert list(proportionnelle_reste_quotient_droop(voix, sum(sieges))) == sieges
