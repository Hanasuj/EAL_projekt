"""Řešič black-box soutěže – sem patří vaše strategie.

Vyhodnocení vyučujícího zavolá ``solve(f, rng_seed)`` pro každou funkci
(f2, f20, f2000), několik tajných instancí a několik seedů algoritmu.
Vyhodnocuje se jen tento soubor; funkce ``solve`` v něm musí zůstat se
stejnou signaturou. Pomocné moduly ze složky ``blackbox/`` importovat smíte.

Co o funkci ``f`` víte (objekt ``omm_blackbox.Problem``):

    f.name                  "f2", "f20" nebo "f2000"
    f.dim                   rozměr (2, 20, 2000)
    f.lower, f.upper        meze (numpy pole délky dim)
    f.budget                celkový rozpočet vyhodnocení (300 / 4 000 / 20 000)
    f.evaluations           kolik vyhodnocení už je spotřebováno
    f(x)                    hodnota v jednom bodě (1 vyhodnocení)
    f.batch(X)              hodnoty v řádcích matice X (n vyhodnocení)
    f.best_x, f.best_y      nejlepší dosud vyhodnocený bod a jeho hodnota

Pravidla (úplné znění je v pravidlech soutěže na webu projektu):
- Každé f(x) i každý řádek f.batch(X) stojí jedno vyhodnocení. Po vyčerpání
  rozpočtu přijde výjimka omm_blackbox.BudgetExhausted; velikost dávky proto
  řiďte podle f.budget - f.evaluations.
- Bod mimo meze, NaN nebo špatný tvar vyhodí ValueError a nepočítá se.
  Body vždy ořízněte do mezí (np.clip).
- Hodnotí se nejlepší SKUTEČNĚ VYHODNOCENÝ bod, ne vrácená hodnota.
  Vracejte f.best_x.
- Pořadí určuje, jak blízko optimu se v rozpočtu dostanete. Když jste
  stejně dobří jako jiný tým, vyhrává rychlejší (menším počtem evaluací
  na dosažení té hodnoty).
- Veškerá náhodnost musí jít z ``rng_seed``, aby šel běh zopakovat.
- Logiku optimalizace pište sami: hotové optimalizační algoritmy
  (scipy.optimize, cma, optuna, nevergrad, pyswarms…) nejsou povolené.
- Importovat smíte jen numpy, standardní knihovnu Pythonu, omm_blackbox
  a vlastní moduly ze složky blackbox/. Nic jiného ve vyhodnocovacím
  prostředí není (ani scipy či matplotlib, i když je máte v projektu);
  hlídá to test blackbox/testy/test_importy.py.

Tento soubor obsahuje ukázkové náhodné hledání. Je to jedna ze dvou
referenčních baseline, kterou je potřeba porazit – nahraďte ho vlastní
strategií (klidně jinou pro každou funkci podle f.name nebo f.dim).
"""

import numpy as np


def solve(f, rng_seed: int) -> np.ndarray:
    rng = np.random.default_rng(rng_seed)
    lower = np.asarray(f.lower, dtype=float)
    upper = np.asarray(f.upper, dtype=float)

    davka = 100  # po dávkách je to mnohem rychlejší než po jednom bodu
    while True:
        zbyva = f.budget - f.evaluations
        if zbyva <= 0:
            break
        n = min(davka, zbyva)  # dávka se musí vejít do zbytku rozpočtu
        X = rng.uniform(lower, upper, size=(n, f.dim))
        f.batch(X)  # nejlepší bod si pamatuje sám objekt f

    return np.asarray(f.best_x)
