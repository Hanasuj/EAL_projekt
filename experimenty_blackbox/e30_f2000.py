"""E30 – f2000: varianty skríningu a podpriestorovej optimalizácie."""
import numpy as np
from ramec import vyhodnot
from spolocne import Vyhodnocovac
import strategie, metody
import os
SEEDY = range(1, 6) if os.environ.get("E30_ZNAME") else range(1, 16)
RNG = range(10) if os.environ.get("E30_ZNAME") else range(3)
def V(**kw):
    def var(f, r):
        ev = Vyhodnocovac(f); rng = np.random.default_rng(r); strategie.strategia_f2000(ev, rng, **kw)
        if ev.zostava() > 0: metody.es_1plus1(ev, rng, x0=ev.best_x, sigma0=0.1)
    return var
import sys
VAR = {
 "E03 aktuálny": {},
 "druhé kolo Newtona na slabých": dict(druhe_kolo=True),
 "k=20 pevne": dict(k_min=20, k_max=20),
 "k=30 pevne": dict(k_min=30, k_max=30),
 "sigma0=1": dict(sigma0=1.0),
 "sigma0=3": dict(sigma0=3.0),
 "reštart CMA z náhodného bodu": dict(restart_z="nahodny"),
 "skríning h=2": dict(h=2.0),
 "skríning h=0.5": dict(h=0.5),
 "k=20, h=2": dict(k_min=20, k_max=20, h=2.0),
 "k=20, h=2, sigma0=3": dict(k_min=20, k_max=20, h=2.0, sigma0=3.0),
 "k=25, h=2": dict(k_min=25, k_max=25, h=2.0),
 "k=15, h=2": dict(k_min=15, k_max=15, h=2.0),
 "k=20, h=2, druhé kolo": dict(k_min=20, k_max=20, h=2.0, druhe_kolo=True),
 "k=20, h=2, BFGS v podpriestore": dict(k_min=20, k_max=20, h=2.0, metoda="bfgs"),
 "k=20, h=2, CMA lambda x4": dict(k_min=20, k_max=20, h=2.0, lam_nasobok=4),
 "k=20, h=2, reštart náhodný": dict(k_min=20, k_max=20, h=2.0, restart_z="nahodny"),
 "BFGS k=20 h=2 + druhé kolo": dict(k_min=20, k_max=20, h=2.0, metoda="bfgs", druhe_kolo=True),
 "BFGS k=25 h=2": dict(k_min=25, k_max=25, h=2.0, metoda="bfgs"),
 "BFGS k=30 h=2": dict(k_min=30, k_max=30, h=2.0, metoda="bfgs"),
 "BFGS k=20 h=1": dict(k_min=20, k_max=20, h=1.0, metoda="bfgs"),
 "BFGS k adapt. [10,40] h=2": dict(h=2.0, metoda="bfgs"),
}
vyber = sys.argv[1:] or list(VAR)
for n in vyber:
    vyhodnot("f2000", V(**VAR[n]), SEEDY, RNG, nazov=n)
