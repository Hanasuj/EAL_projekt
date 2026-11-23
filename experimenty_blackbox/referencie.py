"""Referenčné (najlepšie známe) hodnoty pre validačné inštancie 6–25 z dlhých behov.
Medzera voči nim je iba ODHAD skutočnej medzery (skutočné optimum nepoznáme)."""
import numpy as np
from ramec import Problem, uloz_ref
from spolocne import Vyhodnocovac
import metody, strategie, solve as S
nove = {}
for s in range(6, 26):
    # f2: mriežka 401x401 + Nelder–Mead z 10 najlepších bodov mriežky
    f = Problem("f2", seed=s, budget=10**6); ev = Vyhodnocovac(f)
    g = np.linspace(-5, 5, 401); X, Y = np.meshgrid(g, g); P = np.c_[X.ravel(), Y.ravel()]
    _, z = ev.hodnot(P)
    for i in np.argsort(z)[:10]:
        metody.nelder_mead(ev, P[i], 0.02, rozpocet=2000, tol=1e-13)
    nove[f"f2:{s}"] = f.best_y
    # f20: multištart BFGS, 400 000 vyhodnotení
    f = Problem("f20", seed=s, budget=400000); ev = Vyhodnocovac(f)
    strategie.strategia_f20(ev, np.random.default_rng(7)); nove[f"f20:{s}"] = f.best_y
    print(s, nove[f"f2:{s}"], nove[f"f20:{s}"], flush=True)
for s in range(6, 16):
    f = Problem("f2000", seed=s, budget=300000); S.solve(f, 7); nove[f"f2000:{s}"] = f.best_y
    print(s, nove[f"f2000:{s}"], flush=True)
uloz_ref(nove)
