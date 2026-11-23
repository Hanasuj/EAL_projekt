"""E10/E11 – f2: podiel prieskumu, počet štartov, rozpočet na štart, varianta Nelder–Mead."""
import itertools, sys, numpy as np
from ramec import vyhodnot
from spolocne import Vyhodnocovac
import strategie, solve as S
SEEDY = range(1, 26); RNG = range(10)
vysledky = []
vyhodnot("f2", lambda f, r: S.solve(f, r), SEEDY, RNG, nazov="E03 aktuálny solve.py")
for p, k, rs, v in itertools.product([0.2, 0.3, 0.4, 0.5], [3, 5, 8], [15, 25, 40], ["standard", "prednaska"]):
    def var(f, r, p=p, k=k, rs=rs, v=v):
        ev = Vyhodnocovac(f); rng = np.random.default_rng(r)
        strategie.strategia_f2(ev, rng, podiel_prieskumu=p, pocet_startov=k, rozpocet_na_start=rs, variant_nm=v)
        S.metody.es_1plus1(ev, rng, x0=ev.best_x, sigma0=0.1) if ev.zostava() > 0 else None
    vysledky.append(vyhodnot("f2", var, SEEDY, RNG, nazov=f"p={p} k={k} na_start={rs} {v}", vypis=False))
vysledky.sort(key=lambda d: (-d["uspech"], d["log_priemer"], d["hit_med"]))
for d in vysledky[:12] + vysledky[-3:]:
    print(f"{d['nazov']:38s} <1e-8 {d['uspech']:5.1%} | priem.log10 {d['log_priemer']:6.2f} | najhorší {d['najhorsi']:7.3g} | vyhodn. do 1e-8 {d['hit_med']:5.0f}")
