import csv
import mimetypes
import sys

import pyarrow.parquet as pq
import tomli_w
from pyarrow import ArrowException

from hexagonal.files import ROOT_DIR, get_main_dir
from hexagonal.files.dvc_files import DVCFile, get_dvc_files
from hexagonal.files.spec import (
    ColonneMetadata,
    ColonneType,
    DatasetSpec,
    ProductionSpec,
    SourceSpec,
    load_spec,
)

mimetypes.add_type(
    "application/vnd.apache.parquet",
    ".parquet",
)

PARQUET_TYPES = {
    "STRING": ColonneType.STR,
    "BYTE_ARRAY": ColonneType.STR,
    "INT8": ColonneType.INT,
    "INT16": ColonneType.INT,
    "INT32": ColonneType.INT,
    "INT64": ColonneType.INT,
    "BOOLEAN": ColonneType.BOOL,
    "DOUBLE": ColonneType.FLOAT,
}


def missing_files():
    missing = []
    for d, _, files in (ROOT_DIR / "data" / "01_raw").walk():
        for f in files:
            path = d / f
            if path.suffix == ".toml" and not path.with_suffix(".dvc").is_file():
                missing.append(path.with_suffix(""))

    for prod_dir in ("02_clean", "03_main"):
        for d, _, files in (ROOT_DIR / "data" / prod_dir).walk():
            for f in files:
                path = d / f
                if path.suffix == ".toml" and not path.with_suffix("").is_file():
                    missing.append(path.with_suffix(""))

    return missing


def default_spec(file: DVCFile):
    mimetype, encoding = mimetypes.guess_type(file.path)
    if mimetype and encoding:
        mimetype = f"{mimetype}+{encoding}"
    elif encoding:
        mimetype = f"application/x-{encoding}"

    spec_kwargs = {
        "path": file.path,
        "nom": file.path.stem,
        "description": "\n",
        "mimetype": mimetype,
    }

    if get_main_dir(file.path) == "01_raw":
        if file.path.with_suffix(f"{file.path.suffix}.dvc").is_file():
            return SourceSpec.model_validate(spec_kwargs)
        else:
            return None
    return ProductionSpec.model_validate(spec_kwargs)


def update_csv_columns(file: DVCFile, columns: dict[str, ColonneMetadata]):
    try:
        with open(file.path, "r", newline="") as fd:
            r = csv.reader(fd)
            header = next(r)
    except (csv.Error, UnicodeDecodeError, FileNotFoundError):
        return columns

    updated_columns = {}
    for colonne in header:
        updated_columns[colonne] = columns.get(
            colonne, ColonneMetadata(type=ColonneType.STR)
        )

    return updated_columns


def update_parquet_columns(file: DVCFile, columns: dict[str, ColonneMetadata]):
    try:
        parquet_data = pq.ParquetFile(file.path)
        metadata = parquet_data.schema
    except ArrowException:
        return columns

    updated_columns = {}
    for column in metadata:
        updated_columns[column.name] = columns.get(
            column.name,
            ColonneMetadata(type=ColonneType.STR),
        )
        parquet_type = PARQUET_TYPES.get(
            column.logical_type.type, PARQUET_TYPES[column.physical_type]
        )
        updated_columns[column.name].type = parquet_type

    return updated_columns


def write_spec(spec: DatasetSpec):
    path = spec.path.with_suffix(f"{spec.path.suffix}.toml")
    content = spec.model_dump(exclude_none=True)
    content.pop("path")

    with open(path, "wb") as fd:
        tomli_w.dump(content, fd, multiline_strings=True)


def update_specs():
    for f in missing_files():
        sys.stderr.write(f"Spec présente pour le fichier manquant {f}\n")

    for file in get_dvc_files().values():
        try:
            spec = load_spec(file.path)
        except FileNotFoundError:
            spec = default_spec(file)

        if not spec:
            continue

        if isinstance(spec, SourceSpec) and not spec.editeur:
            sys.stderr.write(f"Source sans editeur: {file.path}\n")

        if isinstance(spec, ProductionSpec) and not spec.section:
            sys.stderr.write(f"Production sans section: {file.path}\n")

        if isinstance(spec, ProductionSpec) and spec.mimetype == "text/csv":
            spec.colonnes = update_csv_columns(file, spec.colonnes or {})

        if (
            isinstance(spec, ProductionSpec)
            and spec.mimetype == "application/vnd.apache.parquet"
        ):
            spec.colonnes = update_parquet_columns(file, spec.colonnes or {})

        write_spec(spec)


if __name__ == "__main__":
    update_specs()
