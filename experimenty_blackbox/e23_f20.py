"""E23 – f20: ochrana pred lokálnymi minimami – krátke paralelné štarty, potom pokračovanie najlepšieho."""
import numpy as np
from ramec import vyhodnot
from spolocne import Vyhodnocovac, latinska_hyperkocka
import metody
SEEDY = range(1, 26); RNG = range(8)
KW = dict(h=1e-7, centralny=False, expanzia=True, parabola=True)
def start(ev, rng, n_init):
    X, y = ev.hodnot(latinska_hyperkocka(rng, n_init, ev.lower, ev.upper)); i = int(np.argmin(y)); return X[i], y[i]
def zaklad(n_init=50):
    def var(f, r):
        ev = Vyhodnocovac(f); rng = np.random.default_rng(r)
        while ev.zostava() > 22:
            x0, f0 = start(ev, rng, min(n_init, ev.zostava() // 10))
            if metody.bfgs_fd(ev, x0, f0=f0, **KW) == "rozpocet": break
    return var
def paralelne(m=3, r1=300, n_init=30):
    def var(f, r):
        ev = Vyhodnocovac(f); rng = np.random.default_rng(r)
        kand = []
        for _ in range(m):
            x0, f0 = start(ev, rng, n_init); zac = ev.pouzite
            metody.bfgs_fd(ev, x0, f0=f0, rozpocet=r1, **KW)
            # najlepší bod tohto behu: posledný prijatý je najlepší v behu -> použijeme f.best ak tento beh
            kand.append((ev.f.best_y, ev.best_x))  # pozn.: globálne najlepší
        while ev.zostava() > 22:
            x0 = ev.best_x
            if metody.bfgs_fd(ev, x0, f0=ev.best_y, **KW) == "rozpocet": break
            x0, f0 = start(ev, rng, 30)
            if metody.bfgs_fd(ev, x0, f0=f0, **KW) == "rozpocet": break
    return var
vyhodnot("f20", zaklad(), SEEDY, RNG, nazov="BFGS+exp+parabola, multištart")
for m, r1 in [(2, 300), (3, 200), (3, 400), (4, 250)]:
    vyhodnot("f20", paralelne(m, r1), SEEDY, RNG, nazov=f"{m} krátke štarty po {r1}, potom najlepší")
