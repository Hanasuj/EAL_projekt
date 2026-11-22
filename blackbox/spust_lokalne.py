"""Lokální vyzkoušení řešiče na veřejných vývojových seedech.

Spuštění z kořene repozitáře:

    uv run python blackbox/spust_lokalne.py                    # všechny funkce, 3 seedy algoritmu
    uv run python blackbox/spust_lokalne.py --funkce f20 --opakovani 5
    uv run python blackbox/spust_lokalne.py --funkce f2 --rozpocet 1000   # jiný rozpočet na zkoušku
    uv run python blackbox/spust_lokalne.py --opakovani 1 --bez-zapisu    # jen ověří, že solve běží

Vypíše tabulku výsledků, uloží ji do blackbox/vystupy/vysledky.csv a nakreslí
graf konvergence blackbox/vystupy/konvergence.svg (s --bez-zapisu nic
neukládá).

Výsledky na vývojových seedech NEJSOU hodnocení. Průběžná kola i finále
běží na tajných seedech, které neznáte – strategie naladěná na pět
vývojových instancí může na jiných propadnout.
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from omm_blackbox import BudgetExhausted, Problem

# Stejné cesty jako při vyhodnocení: složka blackbox/ (pomocné moduly vedle
# solve.py, `import pomocne`) a kořen repozitáře.
BLACKBOX = Path(__file__).resolve().parent
sys.path[:0] = [str(BLACKBOX), str(BLACKBOX.parent)]

from solve import solve  # noqa: E402

# Výstup přesměrovaný do souboru má na Windows cp1252 bez českých znaků.
sys.stdout.reconfigure(encoding="utf-8")

VYVOJOVE_SEEDY = [1, 2, 3, 4, 5]          # veřejné instance pro vývoj
ROZPOCTY = {"f2": 300, "f20": 4000, "f2000": 20000}      # soutěžní rozpočty
CASOVY_LIMIT_S = {"f2": 30, "f20": 60, "f2000": 120}   # limit na jeden běh při vyhodnocení

# Skutečná minima veřejných vývojových instancí (seedy 1–5): „mezera“ ve výpisu
# je proto skutečná vzdálenost od optima. U jiných seedů se počítá vůči
# nejlepší hodnotě, kterou jste na dané instanci v tomto spuštění našli vy sami.
# (Vyučující: přegenerovat blackbox/kalibrace/vyvojova_optima.py při změně soli wheelu.)
OPTIMA_VYVOJ: dict[tuple[str, int], float] = {
    ('f2', 1): 5.024291116290591,
    ('f2', 2): -1.2133799561780165,
    ('f2', 3): 12.83110210731278,
    ('f2', 4): -3.101878057321116,
    ('f2', 5): -3.8790829711275236,
    ('f20', 1): 4.404178732675476,
    ('f20', 2): 28.767353524649977,
    ('f20', 3): 11.301712624462269,
    ('f20', 4): 2.3548290874466176,
    ('f20', 5): 35.409347441170766,
    ('f2000', 1): 93.33691257655715,
    ('f2000', 2): 37.1635093519065,
    ('f2000', 3): 27.76889886524485,
    ('f2000', 4): -26.783665871609315,
    ('f2000', 5): -46.297642428567464,
}


class Zaznam:
    """Obal kolem Problem, který si pamatuje průběh nejlepší hodnoty."""

    def __init__(self, f):
        self._f = f
        self.krivka: list[float] = []

    def __getattr__(self, jmeno):
        return getattr(self._f, jmeno)

    def _zapis(self, hodnoty):
        nejlepsi = self.krivka[-1] if self.krivka else np.inf
        for y in np.atleast_1d(hodnoty):
            nejlepsi = min(nejlepsi, float(y))
            self.krivka.append(nejlepsi)

    def __call__(self, x):
        y = self._f(x)
        self._zapis(y)
        return y

    def batch(self, X):
        ys = self._f.batch(X)
        self._zapis(ys)
        return ys


def jeden_beh(jmeno, seed, rng_seed, rozpocet):
    f = Zaznam(Problem(jmeno, seed=seed, budget=rozpocet))
    stav = "ok"
    t0 = time.perf_counter()
    try:
        x = np.asarray(solve(f, rng_seed=rng_seed), dtype=float)
        if x.shape != (f.dim,):
            stav = f"špatný tvar vráceného bodu {x.shape}"
        elif not np.array_equal(x, np.asarray(f.best_x)):
            stav = "vrácený bod není f.best_x (hodnotí se stejně best_x)"
    except BudgetExhausted:
        stav = "BudgetExhausted (běh platí, ale ošetřete rozpočet)"
    except Exception as e:  # noqa: BLE001
        stav = f"CHYBA {type(e).__name__}: {e}"
    cas = time.perf_counter() - t0
    if cas > CASOVY_LIMIT_S[jmeno]:
        stav += f"; PŘEKROČEN časový limit {CASOVY_LIMIT_S[jmeno]} s"
    # kdy (po kolika vyhodnoceních) byla dosažena konečná nejlepší hodnota
    k = f.krivka
    kdy = next((i + 1 for i, v in enumerate(k) if v <= f.best_y), 0) if k else 0
    return dict(funkce=jmeno, instance=seed, rng_seed=rng_seed, rozpocet=rozpocet,
                vyhodnoceni=f.evaluations, best_y=float(f.best_y), dosazeno_v=kdy,
                cas_s=round(cas, 3), stav=stav, krivka=k)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--funkce", nargs="*", default=list(ROZPOCTY))
    p.add_argument("--opakovani", type=int, default=3, help="počet seedů algoritmu (0, 1, …)")
    p.add_argument("--rozpocet", type=int, default=None, help="jiný rozpočet než soutěžní (jen na zkoušku)")
    p.add_argument("--bez-zapisu", action="store_true",
                   help="jen vypsat, nic neukládat do blackbox/vystupy/ (rychlá zkouška ze spust_vse.py)")
    a = p.parse_args()

    vystupy = Path(__file__).resolve().parent / "vystupy"
    vystupy.mkdir(exist_ok=True)
    vsechny = []
    fig, osy = plt.subplots(1, len(a.funkce), figsize=(5 * len(a.funkce), 4), squeeze=False)

    for ax, jmeno in zip(osy[0], a.funkce):
        rozpocet = a.rozpocet or ROZPOCTY[jmeno]
        print(f"\n== {jmeno}: rozpočet {rozpocet}, limit {CASOVY_LIMIT_S[jmeno]} s na běh ==")
        print(f"{'instance':>8} {'rng':>4} {'best_y':>14} {'mezera':>11} {'dosaženo v':>10} {'čas [s]':>8}  stav")
        behy = [jeden_beh(jmeno, s, r, rozpocet) for s in VYVOJOVE_SEEDY for r in range(a.opakovani)]
        for s in VYVOJOVE_SEEDY:
            ref = OPTIMA_VYVOJ.get((jmeno, s), min(b["best_y"] for b in behy if b["instance"] == s))
            for b in (b for b in behy if b["instance"] == s):
                b["mezera"] = b["best_y"] - ref
                print(f"{s:>8} {b['rng_seed']:>4} {b['best_y']:>14.6g} {b['mezera']:>11.3g} "
                      f"{b['dosazeno_v']:>10} {b['cas_s']:>8.2f}  {b['stav']}")
                if b["krivka"]:
                    ax.plot(np.arange(1, len(b["krivka"]) + 1), np.array(b["krivka"]) - ref + 1e-12,
                            lw=0.8, alpha=0.6)
        med = np.median([b["mezera"] for b in behy])
        print(f"  medián mezery: {med:.3g}" + ("" if OPTIMA_VYVOJ else "  (vůči nejlepšímu vlastnímu výsledku)"))
        ax.set_title(f"{jmeno} (rozpočet {rozpocet})")
        ax.set_xlabel("počet vyhodnocení")
        ax.set_ylabel("mezera k optimu" if OPTIMA_VYVOJ else "mezera k nejlepšímu nalezenému")
        ax.set_xscale("log")
        ax.set_yscale("log")
        vsechny += behy

    if a.bez_zapisu:
        print("\n(--bez-zapisu: tabulka ani graf se neukládají)")
        return
    fig.tight_layout()
    fig.savefig(vystupy / "konvergence.svg")
    with open(vystupy / "vysledky.csv", "w", newline="") as fh:
        pole = ["funkce", "instance", "rng_seed", "rozpocet", "vyhodnoceni", "best_y", "mezera",
                "dosazeno_v", "cas_s", "stav"]
        w = csv.DictWriter(fh, fieldnames=pole, extrasaction="ignore")
        w.writeheader()
        w.writerows(vsechny)
    print(f"\nGraf: {vystupy / 'konvergence.svg'}\nTabulka: {vystupy / 'vysledky.csv'}")


if __name__ == "__main__":
    main()
