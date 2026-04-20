from pathlib import Path
from zipfile import Path as ZPath
from zipfile import ZipFile

import click
from glom import Match, Switch, T, Val

from hexagonal.cog import ANNEE
from hexagonal.utils.clean import iterate_csv, nettoyer_avec_spec

TYPES_EVENEMENTS_COMMUNE = {
    10: "changement de nom",
    20: "création",
    21: "rétablissement",
    30: "suppression",
    31: "fusion simple",
    32: "création commune nouvelle",
    33: "fusion association",
    34: "transformation fusion association en fusion simple",
    35: "suppression commune déléguée",
    41: "changement de département",
    50: "transfert de chef-lieu",
    70: "transformation commune associée en commune déléguée",
    71: "rétablissement commune déléguée",
}


def corriger_nom_commune_com(nom_commune):
    if nom_commune == "Bouloupari":
        return "Boulouparis"
    return nom_commune


spec_region = {
    "code_region": "REG",
    "code_commune_cheflieu": "CHEFLIEU",
    "type_nom": "TNCC",
    "nom": "NCCENR",
}

spec_departement = {
    "code_departement": "DEP",
    "code_region": "REG",
    "code_chef_lieu": "CHEFLIEU",
    "type_nom": "TNCC",
    "nom": "NCCENR",
}

spec_ctcd = {
    "code_ctcd": "CTCD",
    "code_region": "REG",
    "code_chef_lieu": "CHEFLIEU",
    "type_nom": ("TNCC", Match(Switch([("1", Val("2"))], default=T))),
    "nom": "NCCENR",
}

spec_com = {
    "code_departement": "COMER",
    "type_nom": "TNCC",
    "nom": "NCCENR",
}

spec_commune = {
    "code_commune": "COM",
    "type_commune": "TYPECOM",
    "code_region": "REG",
    "code_departement": "DEP",
    "code_collectivite_departementale": "CTCD",
    "code_arrondissement": "ARR",
    "code_canton": "CAN",
    "code_commune_parent": "COMPARENT",
    "type_nom": "TNCC",
    "nom": "NCCENR",
}

spec_commune_com = {
    "code_commune": "COM_COMER",
    "type_commune": "NATURE_ZONAGE",
    "code_departement": "COMER",
    "type_nom": "TNCC",
    "nom": ("NCCENR", corriger_nom_commune_com),
}

spec_canton = {
    "code_canton": "CAN",
    "code_departement": "DEP",
    "code_commune_bureau_centralisateur": "BURCENTRAL",
    "type_canton": "TYPECT",
    "type_nom_canton": "TNCC",
    "nom_canton": "LIBELLE",
}

spec_arrondissement = {
    "code_arrondissement": "ARR",
    "code_departement": "DEP",
    "code_commune_chef_lieu": "CHEFLIEU",
    "type_nom": "TNCC",
    "nom": "NCCENR",
}

spec_commune_historique = {
    "code_commune": "COM",
    "type_nom": "TNCC",
    "nom": "NCCENR",
    "date_debut": "DATE_DEBUT",
    "date_fin": "DATE_FIN",
}

spec_mouvements_communes = {
    "type_evenement": ("MOD", int, TYPES_EVENEMENTS_COMMUNE.get),
    "date_effet": "DATE_EFF",
    "type_commune_avant": "TYPECOM_AV",
    "code_commune_avant": "COM_AV",
    "type_nom_avant": "TNCC_AV",
    "nom_avant": "NCCENR_AV",
    "type_commune_apres": "TYPECOM_AP",
    "code_commune_apres": "COM_AP",
    "type_nom_apres": "TNCC_AP",
    "nom_apres": "NCCENR_AP",
}


fichiers_cog = [
    (f"v_region_{ANNEE}", "regions", spec_region),
    (f"v_departement_{ANNEE}", "departements", spec_departement),
    (f"v_canton_{ANNEE}", "cantons", spec_canton),
    (f"v_arrondissement_{ANNEE}", "arrondissements", spec_arrondissement),
    (f"v_commune_{ANNEE}", "communes", spec_commune),
    (f"v_commune_comer_{ANNEE}", "communes_com", spec_commune_com),
    (f"v_ctcd_{ANNEE}", "ctcd", spec_ctcd),
    (f"v_comer_{ANNEE}", "com", spec_com),
    ("v_commune_depuis_1943", "communes_historiques", spec_commune_historique),
    (f"v_mvt_commune_{ANNEE}", "mouvements_communes", spec_mouvements_communes),
]


@click.command()
@click.argument(
    "archive_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "dest_dir", type=click.Path(file_okay=False, dir_okay=True, path_type=Path)
)
def run(archive_path, dest_dir):
    dest_dir.mkdir(exist_ok=True, parents=True)

    with ZipFile(archive_path) as archive:
        archive_root = ZPath(archive)

        for src, dest, spec in fichiers_cog:
            with iterate_csv(archive_root / f"{src}.csv") as it:
                nettoyer_avec_spec(it, dest_dir / f"{dest}.csv", spec)


if __name__ == "__main__":
    run()
