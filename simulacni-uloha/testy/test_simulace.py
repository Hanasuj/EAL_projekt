"""Testy simulační úlohy. Spuštění z kořene repozitáře: uv run pytest simulacni-uloha

Test načte uložené řešení (``nacti`` z ``reseni.py``, výchozí soubor
``vystupy/reseni.json``), znovu ho ověří funkcí ``kontrola`` (simulátor,
kontrolní seedy) a zkontroluje přípustnost: uloženým číslům se nevěří.
Dokud ve složce není ``simulator.py`` nebo uložené řešení, test se přeskočí.

Doplňte aspoň jeden test, který odhalí chybné řešení (řešení mimo meze
nebo porušující omezení musí ``kontrola`` označit jako nepřípustné).
Dokud ho nedoplníte, ``test_chybne_reseni`` se hlásí jako přeskočený.

Složka se jmenuje ``simulacni-uloha`` (s pomlčkou), takže ji nejde importovat
jako balík; ``reseni.py`` se proto načítá ze souboru funkcí ``nacti_reseni``.
"""

import importlib.util
from pathlib import Path

import pytest

ULOHA = Path(__file__).resolve().parents[1]
RTOL = 1e-6  # kontrola je deterministická; u zašuměné zvětšete podle zadání


def nacti_reseni():
    spec = importlib.util.spec_from_file_location("simulace_reseni", ULOHA / "reseni.py")
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def test_kostra_jde_nacist():
    nacti_reseni()


@pytest.fixture
def uloha():
    if not (ULOHA / "simulator.py").exists():
        pytest.skip("simulator.py ještě není ve složce simulacni-uloha/")
    reseni = nacti_reseni()
    return reseni, reseni.nacti_simulator()


def test_ulozene_reseni_sedi_a_je_pripustne(uloha):
    reseni, sim = uloha
    if not reseni.RESENI.exists():
        pytest.skip(f"chybí {reseni.RESENI.relative_to(ULOHA)}, spusťte simulacni-uloha/reseni.py")
    x, info = reseni.nacti(reseni.RESENI, sim)
    znovu = reseni.kontrola(x, sim)
    assert znovu["poruseni"] <= reseni.TOL, "uložené řešení není přípustné"
    assert znovu["hodnota"] == pytest.approx(info["kontrola"]["hodnota"], rel=RTOL, abs=RTOL), \
        "kontrola dává pro uložené řešení jinou hodnotu, než je zapsaná"


def test_chybne_reseni(uloha):
    pytest.skip("doplňte test chybného řešení")
    # reseni, sim = uloha
    # spatne = ...                                   # mimo meze / porušuje omezení
    # assert reseni.kontrola(spatne, sim)["poruseni"] > reseni.TOL
