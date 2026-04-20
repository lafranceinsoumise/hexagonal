from pathlib import Path

import click

from hexagonal.utils.clean import iterate_csv, nettoyer_avec_spec

spec_codes_postaux = {
    "code_postal": "Code_postal",
    "code_commune": "#Code_commune_INSEE",
    "libelle_acheminement": "Libellé_d_acheminement",
    "ligne5": "Ligne_5",
}


@click.command()
@click.argument(
    "source_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument("dest_path", type=click.Path(path_type=Path))
def run(source_path, dest_path):
    dest_path.parent.mkdir(exist_ok=True, parents=True)
    with iterate_csv(source_path, encoding="latin1", delimiter=";") as it:
        nettoyer_avec_spec(it, dest_path, spec_codes_postaux)


if __name__ == "__main__":
    run()
