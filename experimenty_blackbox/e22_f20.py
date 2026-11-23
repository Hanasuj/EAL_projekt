"""E22 – f20: vylepšenia BFGS (expanzia kroku, skoršie zastavenie, štart)."""
import numpy as np
from ramec import vyhodnot
from spolocne import Vyhodnocovac, latinska_hyperkocka
import metody
SEEDY = range(1, 26); RNG = range(8)
def multistart(n_init=50, **kw):
    def var(f, r):
        ev = Vyhodnocovac(f); rng = np.random.default_rng(r)
        while ev.zostava() > 22:
            k = min(n_init, ev.zostava() // 10)
            if k >= 2:
                X, y = ev.hodnot(latinska_hyperkocka(rng, k, ev.lower, ev.upper)); i = int(np.argmin(y)); x0, f0 = X[i], y[i]
            else:
                x0, f0 = ev.hodnot1(rng.uniform(ev.lower, ev.upper))
            if metody.bfgs_fd(ev, x0, f0=f0, h=1e-7, centralny=False, **kw) == "rozpocet": break
    return var
vyhodnot("f20", multistart(), SEEDY, RNG, nazov="E03 BFGS (aktuálny)")
vyhodnot("f20", multistart(expanzia=True), SEEDY, RNG, nazov="BFGS + expanzia (max 6)")
vyhodnot("f20", multistart(expanzia=True, max_expanzii=12), SEEDY, RNG, nazov="BFGS + expanzia (max 12)")
vyhodnot("f20", multistart(parabola=True), SEEDY, RNG, nazov="BFGS + parabola")
vyhodnot("f20", multistart(expanzia=True, parabola=True), SEEDY, RNG, nazov="BFGS + expanzia + parabola")
vyhodnot("f20", multistart(n_init=20, expanzia=True), SEEDY, RNG, nazov="BFGS + expanzia, LHS 20")
vyhodnot("f20", multistart(n_init=100, expanzia=True), SEEDY, RNG, nazov="BFGS + expanzia, LHS 100")
