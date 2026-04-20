import csv
import json
import logging
import re
from collections import defaultdict
from contextlib import contextmanager
from typing import Iterable

from glom import Iter, glom

DATE_FRANCAISE_RE = re.compile(r"^(?P<jour>\d{2})/(?P<mois>\d{2})/(?P<annee>\d{4})$")
logger = logging.getLogger(__name__)
VRAI = "V"
FAUX = "F"


@contextmanager
def iterate_csv(file, encoding="utf-8", **csv_options):
    should_close = False

    if isinstance(file, (str, bytes)):
        should_close = True
        file = open(file, "r", encoding=encoding, newline="")
    elif hasattr(file, "open"):
        should_close = True
        file = file.open("r", encoding=encoding, newline="")

    try:
        reader = csv.DictReader(file, **csv_options)
        yield reader
    finally:
        if should_close:
            file.close()


@contextmanager
def iterate_ndjson(in_path):
    with open(in_path, "r") as fd:
        yield (json.loads(line) for line in fd)


def nettoyer_avec_spec(it, out_path, spec, columns=None):
    if columns is None:
        columns = list(spec.keys())

    with open(out_path, "w", newline="") as out_f:
        w = csv.DictWriter(out_f, fieldnames=columns)
        w.writeheader()

        w.writerows(glom(it, Iter(spec)))


def vers_booleen(
    *,
    vrai: Iterable[str] | None = None,
    faux: Iterable[str] | None = None,
    default: bool = False,
):
    if vrai is None:
        vrai = ()
    if faux is None:
        faux = ()

    default_value = VRAI if default else FAUX

    mapper = defaultdict(lambda: default_value)
    mapper.update({v: VRAI for v in vrai})
    mapper.update({v: FAUX for v in faux})

    return mapper.__getitem__


def date_francaise_vers_iso(d):
    if not d:
        return ""
    if m := DATE_FRANCAISE_RE.match(d):
        parts = m.groupdict()
        return f"{parts['annee']}-{parts['mois']}-{parts['jour']}"
    else:
        logger.warning(f"Date non valide: {d}")
        return ""


def serie_dates_usuel_vers_iso(d):
    parts = d.str.extract(DATE_FRANCAISE_RE)
    return parts["annee"] + "-" + parts["mois"] + "-" + parts["jour"]
