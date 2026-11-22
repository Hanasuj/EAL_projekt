"""Testy modelové úlohy. Spuštění z kořene repozitáře: uv run pytest model-uloha

Aspoň jeden test musí odhalit chybné řešení: vezměte správné řešení,
pokazte ho (porušte omezení, u MILP dejte neceločíselnou hodnotu, změňte
hodnotu cíle) a ověřte, že ``zkontroluj`` ho odmítne. Dokud ho nedoplníte,
``test_chybne_reseni`` se hlásí jako přeskočený.

Složka se jmenuje ``model-uloha`` (s pomlčkou), takže ji nejde importovat
jako balík; ``reseni.py`` se proto načítá ze souboru funkcí ``nacti_reseni``.
"""

import importlib.util
from pathlib import Path

import pytest

ULOHA = Path(__file__).resolve().parents[1]


def nacti_reseni():
    spec = importlib.util.spec_from_file_location("model_reseni", ULOHA / "reseni.py")
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def test_kostra_jde_nacist():
    nacti_reseni()


def test_chybne_reseni():
    pytest.skip("doplňte test chybného řešení")
    # reseni = nacti_reseni()
    # data = reseni.nacti_data()
    # r = reseni.zakladni_model(data)
    # reseni.zkontroluj(data, r)            # správné řešení projde
    # spatne = ...                          # pokažené řešení
    # with pytest.raises(AssertionError):
    #     reseni.zkontroluj(data, spatne)   # a kontrola ho odmítne
