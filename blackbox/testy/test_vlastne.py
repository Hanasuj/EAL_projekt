"""Vlastné kontroly riešiča nad rámec šablóny (docs/analyza_zadania.md, P02–P07, P13, P14).

Spustenie z koreňa repozitára: uv run pytest blackbox

Testy bežia so zapnutým režimom LADENIE, aby sa chyba v stratégii neskryla
za poistku v solve.py.
"""

import sys
from pathlib import Path

import numpy as np
import pytest

omm_blackbox = pytest.importorskip("omm_blackbox")
from omm_blackbox import Problem  # noqa: E402

BLACKBOX = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(BLACKBOX), str(BLACKBOX.parent)]
import solve as solve_mod  # noqa: E402


@pytest.fixture(autouse=True)
def ladenie(monkeypatch):
    monkeypatch.setattr(solve_mod, "LADENIE", True)


class _Sledovany:
    def __init__(self, p):
        self.p = p
        self.body = []
        self.hodnoty = []

    def __getattr__(self, a):
        return getattr(self.p, a)

    def __call__(self, x):
        y = self.p(x)
        self.body.append(np.asarray(x, float).copy())
        self.hodnoty.append(float(y))
        return y

    def batch(self, X):
        y = self.p.batch(X)
        self.body.extend(np.asarray(X, float).copy())
        self.hodnoty.extend(np.atleast_1d(y).tolist())
        return y


@pytest.mark.parametrize("jmeno,rozpocet", [
    ("f2", 1), ("f2", 2), ("f2", 7), ("f2", 50), ("f2", 300),
    ("f20", 1), ("f20", 21), ("f20", 200), ("f20", 4000),
    ("f2000", 1), ("f2000", 500), ("f2000", 4002), ("f2000", 13000),
])
def test_rozne_rozpocty(jmeno, rozpocet):
    f = _Sledovany(Problem(jmeno, seed=3, budget=rozpocet))
    x = np.asarray(solve_mod.solve(f, rng_seed=1))
    assert f.evaluations == rozpocet, "celý rozpočet má byť využitý a neprekročený"
    assert x.shape == (f.dim,)
    assert np.all(x >= f.lower) and np.all(x <= f.upper)
    assert any(np.array_equal(x, b) for b in f.body)


@pytest.mark.parametrize("jmeno,rozpocet", [("f2", 300), ("f20", 4000), ("f2000", 20000)])
def test_reprodukovatelnost_celej_postupnosti(jmeno, rozpocet):
    behy = []
    for _ in range(2):
        f = _Sledovany(Problem(jmeno, seed=4, budget=rozpocet))
        x = np.asarray(solve_mod.solve(f, rng_seed=11))
        behy.append((x, f.hodnoty))
    assert np.array_equal(behy[0][0], behy[1][0])
    assert behy[0][1] == behy[1][1]


def test_iny_seed_iny_beh():
    a = _Sledovany(Problem("f2", seed=1, budget=300))
    b = _Sledovany(Problem("f2", seed=1, budget=300))
    solve_mod.solve(a, rng_seed=0)
    solve_mod.solve(b, rng_seed=1)
    assert a.hodnoty != b.hodnoty


@pytest.mark.parametrize("seed", [0, 2**31 - 1, 2**63, -5])
def test_velke_rng_seed(seed):
    f = Problem("f2", seed=1, budget=300)
    x = np.asarray(solve_mod.solve(f, rng_seed=seed))
    assert x.shape == (2,)
