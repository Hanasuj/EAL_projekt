"""Kontrola importů řešiče: ve vyhodnocovacím prostředí je numpy,
standardní knihovna Pythonu a modul omm_blackbox. Jinou obecnou knihovnu
(bez hotového optimalizátoru) přidáme na požádání; po schválení ji
dopište do ``PRIDANE``.

Spuštění z kořene repozitáře: uv run pytest blackbox

Projde ``blackbox/solve.py`` a všechny další moduly týmu ve složce
``blackbox/`` (kromě ``spust_lokalne.py`` a ``testy/``, které běží jen
u vás) a ohlásí každý import jiné knihovny: ``import x``, ``from x import``,
``__import__("x")`` i ``importlib.import_module("x")``. scipy, matplotlib,
pandas, cma, optuna … tu máte nainstalované kvůli úlohám M a S, při
vyhodnocení soutěže ale chybí a řešič by tam spadl.
"""

import ast
import sys
from pathlib import Path

import pytest

BLACKBOX = Path(__file__).resolve().parents[1]
JEN_LOKALNE = {"spust_lokalne.py"}
PRIDANE: set[str] = set()  # knihovny přidané na požádání (po domluvě s vyučujícím)
POVOLENE = {"numpy", "omm_blackbox"} | set(sys.stdlib_module_names) | PRIDANE


def moduly_tymu():
    return sorted(p for p in BLACKBOX.rglob("*.py")
                  if "testy" not in p.relative_to(BLACKBOX).parts and p.name not in JEN_LOKALNE)


def vlastni_moduly():
    """Jména, pod kterými jde importovat soubory a složky z blackbox/
    (složka i bez ``__init__.py`` je v Pythonu 3 importovatelný balík)."""
    jmena = {p.stem for p in BLACKBOX.glob("*.py")}
    jmena |= {p.name for p in BLACKBOX.iterdir() if p.is_dir() and p.name.isidentifier()}
    return jmena


def _dynamicky(uzel):
    """Jméno modulu z ``__import__("x")`` nebo ``importlib.import_module("x")``."""
    fce = uzel.func
    jmeno = fce.id if isinstance(fce, ast.Name) else fce.attr if isinstance(fce, ast.Attribute) else None
    if jmeno not in {"__import__", "import_module"} or not uzel.args:
        return None
    arg = uzel.args[0]
    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
        return None if arg.value.startswith(".") else arg.value
    return "<dynamické jméno>"  # jméno se skládá až za běhu, nejde ověřit


def importy(soubor):
    strom = ast.parse(soubor.read_text(encoding="utf-8"), filename=str(soubor))
    for uzel in ast.walk(strom):
        if isinstance(uzel, ast.Import):
            for a in uzel.names:
                yield uzel.lineno, a.name.split(".")[0]
        elif isinstance(uzel, ast.ImportFrom) and uzel.level == 0 and uzel.module:
            yield uzel.lineno, uzel.module.split(".")[0]
        elif isinstance(uzel, ast.Call) and (jmeno := _dynamicky(uzel)):
            yield uzel.lineno, jmeno.split(".")[0]


@pytest.mark.parametrize("soubor", moduly_tymu(), ids=lambda p: str(p.relative_to(BLACKBOX)))
def test_jen_povolene_knihovny(soubor):
    povolene = POVOLENE | vlastni_moduly()
    spatne = [f"{soubor.name}:{radek} import {jmeno}" for radek, jmeno in importy(soubor)
              if jmeno not in povolene]
    assert not spatne, ("ve vyhodnocovacím prostředí je numpy, standardní knihovna "
                        "a knihovny přidané na požádání: " + ", ".join(spatne))
