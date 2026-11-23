"""E01/E02/E03 – porovnanie referencií a stratégií na vývojových inštanciách 1–5.

Spustenie z koreňa repozitára:  uv run python experimenty_blackbox/porovnanie.py
Výstup: blackbox/vystupy/porovnanie_E01_E03.csv a súhrn na obrazovku.
"""
import csv, sys, time
from pathlib import Path
import numpy as np
KOREN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOREN / "blackbox"))
from omm_blackbox import Problem
from spolocne import Vyhodnocovac
import metody, solve as solve_mod

OPT = {('f2', 1): 5.024291116290591, ('f2', 2): -1.2133799561780165, ('f2', 3): 12.83110210731278,
       ('f2', 4): -3.101878057321116, ('f2', 5): -3.8790829711275236, ('f20', 1): 4.404178732675476,
       ('f20', 2): 28.767353524649977, ('f20', 3): 11.301712624462269, ('f20', 4): 2.3548290874466176,
       ('f20', 5): 35.409347441170766, ('f2000', 1): 93.33691257655715, ('f2000', 2): 37.1635093519065,
       ('f2000', 3): 27.76889886524485, ('f2000', 4): -26.783665871609315, ('f2000', 5): -46.297642428567464}
ROZPOCET = {"f2": 300, "f20": 4000, "f2000": 20000}
VARIANTY = {
    "E01 náhodné hľadanie": lambda f, r: metody.nahodne_hladanie(Vyhodnocovac(f), np.random.default_rng(r)),
    "E02 (1+1)-ES": lambda f, r: metody.es_1plus1(Vyhodnocovac(f), np.random.default_rng(r)),
    "E03 solve.py": lambda f, r: solve_mod.solve(f, r),
}

class Zaznam:
    def __init__(s, f): s._f = f; s.y = []
    def __getattr__(s, a): return getattr(s._f, a)
    def __call__(s, x): v = s._f(x); s.y.append(v); return v
    def batch(s, X): v = s._f.batch(X); s.y.extend(np.atleast_1d(v)); return v

def main(opakovani=10, funkcie=("f2", "f20", "f2000")):
    riadky = []
    for fn in funkcie:
        for nazov, var in VARIANTY.items():
            for seed in range(1, 6):
                for r in range(opakovani):
                    f = Zaznam(Problem(fn, seed=seed, budget=ROZPOCET[fn]))
                    t = time.perf_counter(); var(f, r); cas = time.perf_counter() - t
                    b = np.minimum.accumulate(np.array(f.y)) - OPT[(fn, seed)]
                    hit = int(np.argmax(b < 1e-8) + 1) if (b < 1e-8).any() else ""
                    riadky.append(dict(funkcia=fn, varianta=nazov, instancia=seed, rng_seed=r,
                                       medzera=float(b[-1]), vyhodnotenia=len(f.y),
                                       vyhodnoteni_do_1e8=hit, cas_s=round(cas, 3)))
            g = np.array([x["medzera"] for x in riadky if x["funkcia"] == fn and x["varianta"] == nazov])
            c = [x["cas_s"] for x in riadky if x["funkcia"] == fn and x["varianta"] == nazov]
            h = [x["vyhodnoteni_do_1e8"] for x in riadky if x["funkcia"] == fn and x["varianta"] == nazov and x["vyhodnoteni_do_1e8"] != ""]
            L = np.log10(np.maximum(g, 1e-8))
            print(f"{fn:6s} {nazov:22s} medián medzery {np.median(g):9.3g} | najhorší {g.max():9.3g} | "
                  f"medián log10 {np.median(L):6.2f} | <1e-8: {np.mean(g < 1e-8):4.0%} | "
                  f"medián vyhodn. do 1e-8: {np.median(h) if h else '-':>6} | max čas {max(c):.2f} s")
    out = KOREN / "blackbox" / "vystupy" / "porovnanie_E01_E03.csv"
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(riadky[0])); w.writeheader(); w.writerows(riadky)
    print("CSV:", out)

if __name__ == "__main__":
    main()
