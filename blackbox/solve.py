"""Riešič black-box súťaže (EAL/OMM).

Vyhodnotenie vyučujúceho volá ``solve(f, rng_seed)`` pre každú funkciu
(f2, f20, f2000), niekoľko tajných inštancií a niekoľko seedov algoritmu.

Stratégie (podrobne v docs/navrh_strategii.md a docs/teoria.md):

* ``f2``    – latinská hyperkocka (prieskum) + Nelderova–Meadova metóda
              z niekoľkých navzájom vzdialených štartov (strategie.strategia_f2);
* ``f20``   – kvázi-Newtonova metóda BFGS s gradientom z konečných
              diferencií a multištartom (strategie.strategia_f20);
* ``f2000`` – skríning citlivosti premenných, diagonálny Newtonov krok na
              slabých premenných a BFGS v podpriestore dôležitých premenných
              (strategie.strategia_f2000).

Technické pravidlá rieši spoločný ``spolocne.Vyhodnocovac`` (orezanie do
hraníc, neprekročenie rozpočtu). Všetka náhodnosť ide z ``rng_seed``;
o priebehu sa rozhoduje iba podľa počtu vyhodnotení, nikdy podľa času.
Importujú sa len numpy, štandardná knižnica, omm_blackbox a vlastné moduly
z tejto zložky.
"""

import numpy as np

import metody
import strategie
from spolocne import Vyhodnocovac

# Pri vývoji True: chyba v stratégii sa neskryje. Pri odovzdaní False:
# poistka zabráni pádu (pád = neplatný beh = posledné miesto v behu).
LADENIE = False

STRATEGIE = {
    "f2": strategie.strategia_f2,
    "f20": strategie.strategia_f20,
    "f2000": strategie.strategia_f2000,
}


def _vyber_strategiu(f):
    if f.name in STRATEGIE:
        return STRATEGIE[f.name]
    # neznámy názov: rozhodnúť podľa rozmeru
    d = int(f.dim)
    return strategie.strategia_f2 if d <= 5 else strategie.strategia_f20 if d <= 200 \
        else strategie.strategia_f2000


def solve(f, rng_seed: int) -> np.ndarray:
    try:
        rng = np.random.default_rng(rng_seed)
    except (TypeError, ValueError):      # napr. záporné číslo – deterministická náhrada
        rng = np.random.default_rng(abs(int(rng_seed)))
    ev = Vyhodnocovac(f)
    try:
        _vyber_strategiu(f)(ev, rng)
        # ak stratégia skončila skôr, zvyšok rozpočtu použijeme lokálne okolo najlepšieho bodu
        if ev.zostava() > 0 and ev.best_x is not None:
            metody.es_1plus1(ev, rng, x0=ev.best_x, sigma0=0.01 * float(np.mean(ev.sirka)))
        if ev.zostava() > 0:
            metody.nahodne_hladanie(ev, rng)
    except Exception:
        if LADENIE:
            raise
    if f.best_x is None:          # posledná poistka: aspoň jeden vyhodnotený bod
        try:
            ev.hodnot1(ev.stred)
        except Exception:
            if LADENIE:
                raise
    return np.asarray(f.best_x)
