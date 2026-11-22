"""Modelová úloha (M) – hlavní skript.

Spuštění z kořene repozitáře: uv run python model-uloha/reseni.py

Model je přesný (LP, QP nebo MILP) a řeší ho řešič s certifikátem optima:
CVXPY (u MILP proměnné s ``integer=True`` / ``boolean=True`` a řešič HiGHS)
nebo ``scipy.optimize.milp`` / ``linprog``.

Doporučená struktura: data → model → řešení → kontrola → výstupy.
Data z archivu k vaší úloze zkopírujte do model-uloha/data/. Funkce níže jsou
jen návrh; jak kód rozdělíte do funkcí a souborů, je na vás.
"""

from pathlib import Path

import numpy as np

ZDE = Path(__file__).resolve().parent
DATA = ZDE / "data"
VYSTUPY = ZDE / "vystupy"
TOL = 1e-6  # tolerance kontroly omezení (a celočíselnosti u MILP)


def nacti_data():
    raise NotImplementedError("doplňte podle zadání")


def zakladni_model(data):
    """Vyřeší základní model. Vraťte aspoň řešení x a hodnotu cíle,
    u MILP i dolní/horní mez (mezera optimality), pokud ji řešič dává."""
    raise NotImplementedError


def upraveny_model(data):
    """Totéž s novým požadavkem ze zadání."""
    raise NotImplementedError


def zkontroluj(data, reseni):
    """Nezávislá kontrola řešení, nespoléhejte na status řešiče.

    Přepočítejte z x (numpy, ne z objektů řešiče) hodnotu cíle a všechna
    omezení s tolerancí TOL; u MILP i celočíselnost, např.
    ``np.all(np.abs(x - np.round(x)) <= TOL)``. Při porušení vyhoďte
    AssertionError (nebo ValueError) se srozumitelnou zprávou.
    """
    raise NotImplementedError


def main():
    VYSTUPY.mkdir(exist_ok=True)
    data = nacti_data()
    for model in (zakladni_model, upraveny_model):
        reseni = model(data)
        zkontroluj(data, reseni)
    # uložte tabulky a grafy do VYSTUPY


if __name__ == "__main__":
    np.set_printoptions(precision=4, suppress=True)
    main()
