import click
import polars as pl

from hexagonal.utils.polars import polars_large_to_long

PRENOM_RE = r"\p{Uppercase Letter}\p{Lowercase Letter}*"
PRENOMS_RE = rf"(?<prenom>{PRENOM_RE}(?:[ '-]{PRENOM_RE})*)"

NOM_RE = r"[\p{Uppercase Letter}()]+"
NOMS_RE = rf"(?<nom>{NOM_RE}(?: ?[ '-] ?{NOM_RE})*)"

CIVILITE_RE = r"(?<civilite>M.|Mme)"

TDL_RE = rf"^{CIVILITE_RE} {NOMS_RE} {PRENOMS_RE}$"


COLONNES_FIXES = {
    "type_scrutin": pl.String(),
    "code_departement": pl.String(),
    "nom_departement": None,
    "tour": pl.Int16(),
    "inscrits": pl.Int32(),
    "abstentions": pl.Int32(),
    "part_abstentions": None,
    "votants": pl.Int32(),
    "part_votants": None,
    "blancs": pl.Int32(),
    "part_blancs": None,
    "part_blancs_votants": None,
    "nuls": pl.Int32(),
    "part_nuls": None,
    "part_nuls_votants": None,
    "exprimes": None,
    "part_exprimes": None,
    "part_exprimes_votants": None,
}

COLONNES_VARIABLES_MAJ = {
    "numero_depot": pl.Int16(),
    "nuance": pl.String(),
    "sexe": pl.String(),
    "nom": pl.String(),
    "prenom": pl.String(),
    "voix": pl.Int32(),
    "part_voix_inscrits": None,
    "part_voix_exprimes": None,
}

COLONNES_VARIABLES_PROP = {
    "numero_depot": pl.Int16(),
    "nuance": pl.String(),
    "libelle_liste": pl.String(),
    "nom": pl.String(),
    "voix": pl.Int32(),
    "part_voix_inscrits": None,
    "part_voix_exprimes": None,
}


@click.command()
@click.argument("fichier", type=click.Path(exists=True, readable=True))
@click.argument("resultats", type=click.Path(writable=True, dir_okay=False))
def main(fichier, resultats):
    maj_t1 = pl.read_excel(
        fichier, sheet_name="MAJ 1", read_options={"header_row": None, "skip_rows": 2}
    )

    maj_t1 = polars_large_to_long(maj_t1, COLONNES_FIXES, COLONNES_VARIABLES_MAJ)

    maj_t2 = pl.read_excel(
        fichier, sheet_name="MAJ 2", read_options={"header_row": None, "skip_rows": 2}
    )
    maj_t2 = polars_large_to_long(maj_t2, COLONNES_FIXES, COLONNES_VARIABLES_MAJ)

    prop = pl.read_excel(
        fichier, sheet_name="PROP", read_options={"header_row": None, "skip_rows": 2}
    )
    prop = polars_large_to_long(prop, COLONNES_FIXES, COLONNES_VARIABLES_PROP)
    prop = prop.with_columns(pl.col("nom").str.extract_groups(TDL_RE)).with_columns(
        prenom=pl.col("nom").struct.field("prenom"),
        nom=pl.col("nom").struct.field("nom"),
        sexe=pl.col("nom")
        .struct.field("civilite")
        .replace_strict(["M.", "Mme"], ["M", "F"]),
    )

    res = (
        pl.concat([maj_t1, maj_t2, prop], how="diagonal_relaxed")
        .sort(["code_departement", "tour", "numero_depot"])
        .filter(pl.col("numero_depot").is_not_null())
        .with_columns(pl.col("code_departement").str.zfill(2))
    )

    res.write_parquet(resultats)


if __name__ == "__main__":
    main()
