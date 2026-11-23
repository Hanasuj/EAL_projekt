"""Stratégie pre jednotlivé funkcie (návrh: docs/navrh_strategii.md).

Všetky podiely rozpočtu sa počítajú z f.budget, takže stratégie fungujú aj
pri menších rozpočtoch (testy používajú 50/200/300/500).
"""

from __future__ import annotations

import math

import numpy as np

import metody
from spolocne import Podpriestor, Vyhodnocovac, latinska_hyperkocka, vyber_vzdialenych


# ---------------------------------------------------------------------------
# f2 – prieskum (LHS) + Nelder–Mead z viacerých vzdialených štartov
# (navrh_strategii.md, časť 2; teoria.md, časti 2, 4, 10)
# ---------------------------------------------------------------------------
def strategia_f2(ev: Vyhodnocovac, rng, podiel_prieskumu: float = 0.4,
                 pocet_startov: int = 5, rozpocet_na_start: int = 15,   # E10/E11
                 variant_nm: str = "standard"):
    B = ev.zostava()
    n = ev.dim
    n0 = int(round(podiel_prieskumu * B))
    n0 = max(min(n0, B), min(B, 2 * (n + 1)))
    X, y = ev.hodnot(latinska_hyperkocka(rng, n0, ev.lower, ev.upper))
    if y.size == 0:
        return
    # typická vzdialenosť susedných bodov LHS v n rozmeroch
    d_min = float(np.mean(ev.sirka)) / max(1.0, n0 ** (1.0 / n))
    starty = vyber_vzdialenych(X, y, pocet_startov, d_min)

    # 1) krátke spresnenie každého štartu
    vysledky = []
    for i in starty:
        if ev.zostava() <= n + 1:
            break
        xb, fb, vel = metody.nelder_mead(ev, X[i], 0.5 * d_min, rozpocet=rozpocet_na_start,
                                         variant=variant_nm, f0=y[i])
        vysledky.append((fb, xb, vel))
    if not vysledky:
        return
    vysledky.sort(key=lambda t: t[0])

    # 2) dokončenie najlepšieho; po konvergencii reštart simplexu, potom ďalší kandidát
    fronta = [(fb, xb, max(vel, 1e-3)) for fb, xb, vel in vysledky]
    while ev.zostava() > n + 1 and fronta:
        fb, xb, vel = fronta.pop(0)
        while ev.zostava() > n + 1:
            xn, fn, vel_n = metody.nelder_mead(ev, xb, max(vel, 1e-6), variant=variant_nm,
                                               f0=fb, tol=1e-11)
            zlepsenie = fb - fn
            xb, fb = xn, fn
            if zlepsenie <= 1e-12 * max(1.0, abs(fb)):
                break               # reštart už nič nepriniesol
            vel = max(10 * vel_n, 1e-6)


# ---------------------------------------------------------------------------
# f20 – BFGS s doprednými diferenciami (h = 1e-7) a multištartom; hľadanie na
# priamke s expanziou kroku a parabolickou interpoláciou (E22).
# Pôvodný návrh bol CMA-ES; experiment E21 ukázal, že funkcia je hladká
# (D02) a BFGS je pri rozpočte 4000 o mnoho rádov lepšia (docs/experimenty.md).
# CMA-ES ostáva ako alternatíva (strategia_f20_cma).
# ---------------------------------------------------------------------------
def strategia_f20(ev: Vyhodnocovac, rng, n_init: int = 50, h: float = 1e-7):
    n = ev.dim
    while ev.zostava() > n + 2:
        k = min(n_init, ev.zostava() // 10)
        if k >= 2:
            X, y = ev.hodnot(latinska_hyperkocka(rng, k, ev.lower, ev.upper))
            if y.size == 0:
                return
            i = int(np.argmin(y))
            x0, f0 = X[i], float(y[i])
        else:
            x0, f0 = ev.hodnot1(rng.uniform(ev.lower, ev.upper))
            if x0 is None:
                return
        dovod = metody.bfgs_fd(ev, x0, f0=f0, h=h, centralny=False,
                               expanzia=True, parabola=True)   # E22
        if dovod == "rozpocet":
            return
        # BFGS skonvergovala (lokálne minimum) – ďalší štart z nového miesta


def strategia_f20_cma(ev: Vyhodnocovac, rng, n_init: int | None = None, sigma0: float = 2.0,
                      restart_z: str = "best"):
    n = ev.dim
    B = ev.zostava()
    n_init = 2 * n if n_init is None else n_init
    n_init = min(n_init, max(1, B // 10))
    X, y = ev.hodnot(latinska_hyperkocka(rng, n_init, ev.lower, ev.upper))
    if y.size == 0:
        return
    m0 = X[int(np.argmin(y))]
    metody.cma_es_ipop(ev, rng, m0=m0, sigma0=sigma0, restart_z=restart_z)


# ---------------------------------------------------------------------------
# f2000 – skríning citlivosti (h = 2) + diagonálny Newtonov krok na slabých
#         premenných + BFGS s multištartom v podpriestore dôležitých premenných
#         (pôvodne CMA-ES; zmena podľa E30)
# (navrh_strategii.md, časť 4; teoria.md, časť 9; diagnostika D03)
# ---------------------------------------------------------------------------
def skrining(ev: Vyhodnocovac, x0, h: float, blok: int = 250):
    """Centrálny skríning: f(x0), f(x0 ± h e_i) pre všetky i (2n + 1 vyhodnotení).

    Vráti (f0, g, c, E) – odhad derivácie, druhej derivácie a efekt
    E_i = max(|f+ - f0|, |f- - f0|). Ak minie rozpočet, vráti None.
    """
    n = ev.dim
    _, f0 = ev.hodnot1(x0)
    if f0 is None:
        return None
    fp = np.empty(n)
    fm = np.empty(n)
    for zac in range(0, n, blok):
        idx = np.arange(zac, min(n, zac + blok))
        for znam, ciel in ((+1, fp), (-1, fm)):
            X = np.repeat(x0[None, :], len(idx), axis=0)
            X[np.arange(len(idx)), idx] += znam * h
            _, yy = ev.hodnot(X)
            if yy.size < len(idx):
                return None
            ciel[idx] = yy
    g = (fp - fm) / (2 * h)
    c = (fp - 2 * f0 + fm) / h ** 2
    E = np.maximum(np.abs(fp - f0), np.abs(fm - f0))
    return f0, g, c, E


def strategia_f2000(ev: Vyhodnocovac, rng, h: float = 2.0, k_min: int = 10, k_max: int = 40,
                    prah: float = 1e-3, sigma0: float = 2.0, druhe_kolo: bool = False,
                    restart_z: str = "best", h2: float = 0.5, metoda: str = "bfgs",   # E30
                    lam_nasobok: int = 1):
    n = ev.dim
    B = ev.zostava()
    if B < 3 * (2 * n + 1):        # malý rozpočet (testy): skríning sa neoplatí
        metody.es_1plus1(ev, rng)
        return
    x0 = ev.stred.copy()
    vys = skrining(ev, x0, h)
    if vys is None:
        return
    f0, g, c, E = vys

    # dôležité premenné: E_i > prah * max E, počet obmedzený na [k_min, k_max]
    poradie = np.argsort(-E, kind="stable")
    k = int(np.sum(E > prah * E[poradie[0]]))
    k = max(k_min, min(k_max, k))
    S = np.sort(poradie[:k])
    slabe = np.setdiff1d(np.arange(n), S)

    # diagonálny Newtonov krok iba na slabých premenných (D03c: takmer kvadratické)
    x1 = x0.copy()
    ok = c[slabe] > 1e-12
    krok = np.where(ok, -g[slabe] / np.where(ok, c[slabe], 1.0), 0.0)
    x1[slabe] = np.clip(x0[slabe] + krok, ev.lower[slabe], ev.upper[slabe])
    # silné premenné: lepšia z troch hodnôt skríningu ako štart
    xs, f1 = ev.hodnot1(x1)
    zaklad = xs if (f1 is not None and f1 <= f0) else x0

    # CMA-ES v k-rozmernom podpriestore so zvyšným rozpočtom
    rezerva = 2 * len(slabe) + 2 if druhe_kolo else 0
    pod = Podpriestor(ev, S, zaklad)
    limit = ev.pouzite + max(0, ev.zostava() - rezerva)
    if metoda == "bfgs":
        x0, f0 = zaklad[S], None
        while limit - ev.pouzite > 2 * k + 2:
            dovod = metody.bfgs_fd(pod, x0, f0=f0, rozpocet=limit - ev.pouzite, h=1e-7,
                                   centralny=False, expanzia=True, parabola=True)
            if dovod == "rozpocet":
                break
            X, y = pod.hodnot(latinska_hyperkocka(rng, 20, pod.lower, pod.upper))
            if y.size == 0:
                break
            i = int(np.argmin(y))
            x0, f0 = X[i], float(y[i])
    else:
        lam = (4 + int(3 * math.log(k))) * lam_nasobok
        if lam_nasobok > 1:
            metody.cma_es(pod, rng, zaklad[S], sigma0, rozpocet=limit - ev.pouzite, lam=lam)
        metody.cma_es_ipop(pod, rng, m0=pod.best_x if pod.best_x is not None else zaklad[S],
                           sigma0=sigma0, restart_z=restart_z,
                           rozpocet=max(0, limit - ev.pouzite))
    if druhe_kolo and ev.zostava() >= rezerva and ev.best_x is not None:
        # druhé kolo Newtonovho kroku na slabých premenných z nového najlepšieho bodu
        xb, fb = ev.best_x, ev.best_y
        fp = np.empty(len(slabe)); fm = np.empty(len(slabe))
        for znam, ciel in ((+1, fp), (-1, fm)):
            X = np.repeat(xb[None, :], len(slabe), axis=0)
            X[np.arange(len(slabe)), slabe] += znam * h2
            _, yy = ev.hodnot(X)
            if yy.size < len(slabe):
                return
            ciel[:] = yy
        g2 = (fp - fm) / (2 * h2)
        c2 = (fp - 2 * fb + fm) / h2 ** 2
        x2 = xb.copy()
        ok = c2 > 1e-12
        x2[slabe] = np.clip(xb[slabe] + np.where(ok, -g2 / np.where(ok, c2, 1.0), 0.0),
                            ev.lower[slabe], ev.upper[slabe])
        ev.hodnot1(x2)
