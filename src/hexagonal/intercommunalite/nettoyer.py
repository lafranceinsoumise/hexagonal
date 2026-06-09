from zipp.compat.overlay import zipfile
from pathlib import Path

import click
import polars as pl


insee_columns = {
    "siren_epci": "EPCI",
    "nom_epci": "LIBEPCI",
    "code_commune": "CODGEO",
    "nom_commune": "LIBGEO",
}

banatic_columns = {
    "siren_epci": "N° SIREN",
    "nom_epci": "Nom du groupement",
    "nature_epci": "Nature juridique",
    "mode_financement": "Mode de financement",
    "date_creation": "Date de création",
    "date_effet": "Date d'effet",
    "siren_commune": "Siren membre",
    "nom_commune": "Nom membre",
}

NATURES_JURIDIQUES = [
    "CC",  # Communauté de communes
    "CA",  # Communauté d'agglomération
    "CU",  # Communauté urbaine
    "METRO",  # Métropole
    "MET69",  # Métropole de Lyon, EPCI sui generis
    "EPT",  # Établissement public de territoire (Grand Paris)
]

# il y a bien deux cas de villes aux noms identiques qui se retrouvent dans le même EPCI
deduplication_keys = pl.Series(
    [
        ("38446", "213804461"),  # Saint-Pierre d'Entremont, Isère
        ("73274", "217302744"),  # Saint-Pierre d'Entremont, Savoie
        ("01407", "210104071"),  # Seyssel, Ain
        ("74269", "217402692"),  # Seyssel, Haute-Savoie
    ],
    dtype=pl.Struct({"code_commune": pl.String, "siren_commune": pl.String}),
)

missing = [
    {
        "code_commune": "56068",
        "siren_commune": "215600685",
        "siren_epci": "200066777",
        "nature_epci": "CC",
    }
]


@click.command()
@click.option("--banatic", type=click.Path(exists=True, readable=True, dir_okay=False))
@click.option("--insee", type=click.Path(exists=True, readable=True, dir_okay=False))
@click.option("--epci", type=click.Path(writable=True, dir_okay=False, path_type=Path))
@click.option(
    "--composition", type=click.Path(writable=True, dir_okay=False, path_type=Path)
)
def nettoyer(banatic, insee, epci, composition):
    epci_banatic = (
        pl.read_excel(
            banatic,
            columns=[
                *banatic_columns.values(),
                "Catégorie des membres du groupement",
            ],
        )
        .filter(
            (pl.col("Catégorie des membres du groupement") == "commune")
            & pl.col("Nature juridique").is_in(NATURES_JURIDIQUES)
        )
        .select(**banatic_columns)
        .with_columns()
    )

    epci_banatic.unique("siren_epci").select(
        "siren_epci",
        "nom_epci",
        "nature_epci",
        "mode_financement",
        "date_creation",
        "date_effet",
    ).sort("siren_epci").write_csv(epci)

    with zipfile.ZipFile(insee) as archive:
        with archive.open("EPCI_au_01-01-2026.xlsx") as fd:
            composition_insee = (
                pl.read_excel(
                    fd.read(),
                    sheet_name="Composition_communale",
                    read_options={"header_row": 5},
                    columns=list(insee_columns.values()),
                )
                .select(**insee_columns)
                .filter(pl.col("nom_epci") != "Sans objet")
            )

    composition_epci = (
        composition_insee.join(
            epci_banatic,
            on=["siren_epci", "nom_commune"],
        )
        .filter(
            ~pl.struct("siren_epci", "code_commune").is_duplicated()
            | pl.struct("code_commune", "siren_commune").is_in(
                deduplication_keys.implode()
            )
        )
        .select(
            "code_commune",
            "siren_commune",
            "siren_epci",
            "nature_epci",
        )
    )

    composition_epci = pl.concat([composition_epci, pl.DataFrame(missing)])
    composition_epci.sort("code_commune").write_csv(composition)


if __name__ == "__main__":
    nettoyer()
