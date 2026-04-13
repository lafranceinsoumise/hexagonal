import click
from glom import Coalesce, S, T, glom

from hexagonal.codes import CORRESPONDANCE_CODE_DEPARTEMENT
from hexagonal.utils import (
    date_francaise_vers_iso,
    iterate_csv,
    nettoyer_avec_spec,
    vers_booleen,
)


class ContextBuilder:
    def glomit(self, target, scope):
        departement = scope[glom](
            target, Coalesce("Code du département", "Code département"), scope
        )
        departement = normalisation_code_departement(departement)

        circonscription = target["Code circonscription"]
        circonscription = normalisation_code_circonscription_ministere(
            circonscription, departement
        )

        scope.update({"circonscription": circonscription, "departement": departement})
        return target


def normalisation_code_departement(code_departement: str):
    return CORRESPONDANCE_CODE_DEPARTEMENT.get(
        code_departement, code_departement
    ).zfill(2)


def normalisation_code_circonscription_ministere(
    code_circonscription, code_departement
):
    """
    normalise les codes de circonscription conformément à la documentation

    :param code_circonscription:
    :return:
    """
    numero = code_circonscription[-2:].zfill(2)
    if code_departement in ["977", "978"]:
        code_departement = "ZX"
    return f"{code_departement}-{numero}"


booleen = vers_booleen(vrai=["oui"])


base_spec = {
    "departement": S.departement,
    "circonscription": S.circonscription,
    "numero_panneau": Coalesce("N° panneau", "Numéro de panneau"),
    "numero_depot": Coalesce("N° candidat", "N° dépôt"),
    "sexe": Coalesce("Sexe candidat", "Sexe du candidat"),
    "nom": Coalesce("Nom candidat", "Nom du candidat"),
    "prenom": Coalesce("Prénom candidat", "Prénom du candidat"),
    "date_naissance": (
        Coalesce("Date naissance candidat", "Date de naissance du candidat"),
        date_francaise_vers_iso,
    ),
    "nuance": Coalesce("Nuance candidat", "Code nuance"),
    "profession": Coalesce("Profession candidat", "Profession"),
    "sortant": (
        Coalesce("Le candidat est sortant", "Sortant"),
        T.lower(),
        booleen,
    ),
    "sexe_suppleant": "Sexe remplaçant",
    "nom_suppleant": "Nom remplaçant",
    "prenom_suppleant": "Prénom remplaçant",
    "date_naissance_suppleant": (
        Coalesce(
            T[
                "Date naiss. remplaçant"
            ],  # Attention à la présence d'un . dans le nom du champ
            "Date de naissance remplaçant",
        ),
        date_francaise_vers_iso,
    ),
    "sortant_suppleant": (
        Coalesce("Le remplaçant est sortant", "Sortant remplaçant"),
        T.lower(),
        booleen,
    ),
}


@click.command()
@click.argument(
    "src_file", type=click.Path(exists=True, file_okay=True, dir_okay=False)
)
@click.argument("dest_file", type=click.Path(file_okay=True, dir_okay=False))
@click.option("-d", "--delimiter", default=",")
@click.option("-e", "--encoding", default="utf-8")
def nettoyer(src_file, dest_file, delimiter, encoding):
    with iterate_csv(src_file, encoding=encoding, delimiter=delimiter) as it:
        nettoyer_avec_spec(
            it,
            dest_file,
            (ContextBuilder(), base_spec),
            columns=list(base_spec.keys()),
        )


if __name__ == "__main__":
    nettoyer()
