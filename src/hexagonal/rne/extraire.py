from pathlib import Path

import click
import pandas as pd
from glom import T, glom

from hexagonal.utils.clean import serie_dates_usuel_vers_iso

TYPE_CSP = {
    "69M": "MSP",
    "94": "CTU",
    "972": "CTU",
    "973": "CTU",
    "975": "COMER",
    "977": "COMER",
    "978": "COMER",
    "986": "COMER",
    "987": "COMER",
    "988": "CNP",
}

CODE_CSP = {
    "69M": "69M",
    "94": "20R",
    "972": "972R",
    "973": "973R",
    "975": "975C",
    "977": "977C",
    "978": "978C",
    "986": "986C",
    "987": "987C",
    "988": "988C",
}


def code_secteur(elus):
    return (
        elus["Code de la commune"]
        + "SR"
        + elus["Libellé du secteur"].str.extract(r"(\d+)")[0].str.zfill(2)
    )


spec_conseiller_arrondissement = {
    "code_commune": "Code de la commune",
    "code_secteur": code_secteur,
    "nom": "Nom de l'élu",
    "prenom": "Prénom de l'élu",
    "sexe": "Code sexe",
    "date_naissance": "Date de naissance",
    "csp": "Code de la catégorie socio-professionnelle",
    "date_debut_mandat": ("Date de début du mandat", serie_dates_usuel_vers_iso),
    "fonction": "Libellé de la fonction",
    "date_debut_fonction": ("Date de début de la fonction", serie_dates_usuel_vers_iso),
}

spec_conseiller_municipal = {
    "code_departement": ("Code du département", T.str.zfill(2)),
    "code_collectivite_sp": "Code de la collectivité à statut particulier",
    "code_commune": ("Code de la commune", T.str.zfill(5)),
    "nom": "Nom de l'élu",
    "prenom": "Prénom de l'élu",
    "sexe": "Code sexe",
    "date_naissance": ("Date de naissance", serie_dates_usuel_vers_iso),
    "csp": "Code de la catégorie socio-professionnelle",
    "date_debut_mandat": ("Date de début du mandat", serie_dates_usuel_vers_iso),
    "fonction": "Libellé de la fonction",
    "date_debut_fonction": ("Date de début de la fonction", serie_dates_usuel_vers_iso),
    "nationalite": "Code nationalité",
}


spec_conseiller_departemental = {
    "code_departement": ("Code du département", T.str.zfill(2)),
    "code_canton": ("Code du canton", T.str.zfill(4)),
    "nom": "Nom de l'élu",
    "prenom": "Prénom de l'élu",
    "sexe": "Code sexe",
    "date_naissance": ("Date de naissance", serie_dates_usuel_vers_iso),
    "csp": "Code de la catégorie socio-professionnelle",
    "date_debut_mandat": ("Date de début du mandat", serie_dates_usuel_vers_iso),
    "fonction": "Libellé de la fonction",
    "date_debut_fonction": ("Date de début de la fonction", serie_dates_usuel_vers_iso),
}

spec_conseiller_regional = {
    "code_region": ("Code de la région", T.str.zfill(2)),
    "code_departement": ("Code de la section départementale", T.str.zfill(2)),
    "nom": "Nom de l'élu",
    "prenom": "Prénom de l'élu",
    "sexe": "Code sexe",
    "date_naissance": ("Date de naissance", serie_dates_usuel_vers_iso),
    "csp": "Code de la catégorie socio-professionnelle",
    "date_debut_mandat": ("Date de début du mandat", serie_dates_usuel_vers_iso),
    "fonction": "Libellé de la fonction",
    "date_debut_fonction": ("Date de début de la fonction", serie_dates_usuel_vers_iso),
}

spec_conseiller_csp = {
    "type_csp": T["Code de la collectivité à statut particulier"].map(TYPE_CSP),
    "code_csp": T["Code de la collectivité à statut particulier"].map(CODE_CSP),
    "code_section": T["Code de la circonscription métropolitaine"].fillna(
        T["Code de la section - collectivité à statut particulier"]
    ),
    "nom": "Nom de l'élu",
    "prenom": "Prénom de l'élu",
    "sexe": "Code sexe",
    "date_naissance": ("Date de naissance", serie_dates_usuel_vers_iso),
    "csp": "Code de la catégorie socio-professionnelle",
    "date_debut_mandat": ("Date de début du mandat", serie_dates_usuel_vers_iso),
    "fonction": "Libellé de la fonction",
    "date_debut_fonction": ("Date de début de la fonction", serie_dates_usuel_vers_iso),
}

SPECS = {
    "conseillers_arrondissement": spec_conseiller_arrondissement,
    "conseillers_municipaux": spec_conseiller_municipal,
    "conseillers_departementaux": spec_conseiller_departemental,
    "conseillers_regionaux": spec_conseiller_regional,
    "conseillers_csp": spec_conseiller_csp,
}


def extraire(in_path, out_path, spec):
    # un des fichiers du millésime de décembre 2025 a été exporté avec le séparateur virgule…
    data_in = pd.read_csv(in_path, delimiter=";", dtype=str)

    data_out = pd.DataFrame(glom(data_in, spec))

    data_out.to_csv(out_path, index=False)


@click.command()
@click.argument(
    "src_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
)
@click.argument(
    "dest_dir", type=click.Path(file_okay=False, dir_okay=True, path_type=Path)
)
@click.argument("type_mandat", type=click.Choice(list(SPECS.keys())))
def run(src_dir, dest_dir, type_mandat):
    dest_dir.mkdir(exist_ok=True, parents=True)

    extraire(
        src_dir / f"{type_mandat}.csv",
        dest_dir / f"{type_mandat}.csv",
        SPECS[type_mandat],
    )


if __name__ == "__main__":
    run()
