"""Základní kontroly řešiče – stejné věci hlídá i vyhodnocení vyučujícího.

Spuštění z kořene repozitáře: uv run pytest blackbox

Rozpočty jsou tu menší než soutěžní, aby testy běžely rychle. Když vaše
strategie s malým rozpočtem nepočítá a vyletí z ní BudgetExhausted, test
neselže: podle pravidel soutěže to chyba není a hodnotí se nejlepší
vyhodnocený bod. Hlídá se jen, že rozpočet nebyl překročen.
"""

import sys
from pathlib import Path

import numpy as np
import pytest

omm_blackbox = pytest.importorskip("omm_blackbox", reason="modul omm_blackbox není nainstalovaný")
from omm_blackbox import BudgetExhausted, Problem  # noqa: E402

# Složka blackbox/ do cesty, aby šel solve.py i jeho pomocné moduly importovat
# stejně jako při vyhodnocení a v spust_lokalne.py.
BLACKBOX = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(BLACKBOX), str(BLACKBOX.parent)]
from solve import solve  # noqa: E402


class _SledovanyProblem:
    """Pro test zaznamená úspěšná vyhodnocení, i část dávky před výjimkou."""

    def __init__(self, problem):
        self.problem = problem
        self.body = []

    def __getattr__(self, jmeno):
        return getattr(self.problem, jmeno)

    def __call__(self, x):
        bod = np.asarray(x).copy()
        pred = self.problem.evaluations
        try:
            return self.problem(x)
        finally:
            if self.problem.evaluations > pred:
                self.body.append(bod)

    def batch(self, X):
        body = np.asarray(X).copy()
        pred = self.problem.evaluations
        try:
            return self.problem.batch(X)
        finally:
            pocet = self.problem.evaluations - pred
            self.body.extend(body[:pocet])


@pytest.mark.parametrize("jmeno,rozpocet", [("f2", 50), ("f20", 200), ("f2000", 500)])
def test_dodrzi_rozpocet_a_vrati_vyhodnoceny_bod(jmeno, rozpocet):
    f = _SledovanyProblem(Problem(jmeno, seed=1, budget=rozpocet))
    try:
        x = np.asarray(solve(f, rng_seed=0))
    except BudgetExhausted:
        # Běh platí, hodnotí se nejlepší vyhodnocený bod.
        x = np.asarray(f.best_x)
    assert f.evaluations <= rozpocet
    assert f.best_x is not None, "řešič nevyhodnotil ani jeden bod"
    assert x.shape == (f.dim,)
    assert np.all(np.isfinite(x))
    assert np.all(x >= f.lower) and np.all(x <= f.upper)
    assert any(np.array_equal(x, bod) for bod in f.body), "vracejte skutečně vyhodnocený bod"


def _beh(jmeno, rng_seed):
    f = Problem(jmeno, seed=2, budget=300)
    try:
        x = np.asarray(solve(f, rng_seed=rng_seed))
    except BudgetExhausted:
        x = np.asarray(f.best_x)
    return x, f.best_y


@pytest.mark.parametrize("jmeno", ["f2", "f20"])
def test_stejny_seed_stejny_vysledek(jmeno):
    xa, ya = _beh(jmeno, 7)
    xb, yb = _beh(jmeno, 7)
    assert np.array_equal(xa, xb)
    assert ya == yb
