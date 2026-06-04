import tomllib
from importlib import resources
from pathlib import Path
from typing import cast

ROOT_DIR = Path(".").resolve()

while not (ROOT_DIR / "pyproject.toml").is_file() and ROOT_DIR != ROOT_DIR.parent:
    ROOT_DIR = ROOT_DIR.parent

if (ROOT_DIR / "pyproject.toml").is_file():
    with open(ROOT_DIR / "pyproject.toml", "rb") as fd:
        CONFIG = tomllib.load(fd)["tool"]["hexagonal"]
else:
    # noinspection PyInvalidCast
    ROOT_DIR = cast(Path, resources.files("hexagonal"))
    CONFIG = None


DATA_DIR = ROOT_DIR / "data"


def relative_path(path: Path | str) -> Path:
    if isinstance(path, str):
        path = Path(path)
    return path.resolve().relative_to(ROOT_DIR)


def get_main_dir(path: Path) -> str:
    path = path.resolve().relative_to(ROOT_DIR)

    parents = list(path.parents)
    assert parents[-2].name == "data"
    return parents[-3].name
