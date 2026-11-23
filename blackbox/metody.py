"""Základné optimalizačné metódy (vlastná implementácia, iba numpy).

Teória a význam premenných sú v docs/teoria.md; čísla častí sú uvedené pri
každej funkcii. Všetky metódy vyhodnocujú body len cez ``Vyhodnocovac``
(spolocne.py) a končia, keď minú pridelený rozpočet ``rozpocet`` alebo
celý zvyšok rozpočtu funkcie.
"""

from __future__ import annotations

import math

import numpy as np

from spolocne import Vyhodnocovac, latinska_hyperkocka


def _limit(ev: Vyhodnocovac, rozpocet) -> int:
    """Počet vyhodnotení, ktoré smie metóda ešte minúť (od teraz)."""
    zost = ev.zostava()
    return zost if rozpocet is None else max(0, min(int(rozpocet), zost))


# ---------------------------------------------------------------------------
# teoria.md, časť 1 – náhodné hľadanie (referencia 1)
# ---------------------------------------------------------------------------
def nahodne_hladanie(ev: Vyhodnocovac, rng, rozpocet=None, davka: int = 100):
    koniec = ev.pouzite + _limit(ev, rozpocet)
    while ev.pouzite < koniec and ev.zostava() > 0:
        k = min(davka, koniec - ev.pouzite)
        ev.hodnot(rng.uniform(ev.lower, ev.upper, size=(k, ev.dim)))


# ---------------------------------------------------------------------------
# teoria.md, časť 7.1 – (1+1)-ES s pravidlom 1/5 (referencia 2)
#   y = x + sigma*z,  z ~ N(0, I);   x <- y ak f(y) <= f(x)
#   sigma <- sigma * exp((1[úspech] - 1/5) / d),  d = sqrt(n + 1)
# ---------------------------------------------------------------------------
def es_1plus1(ev: Vyhodnocovac, rng, rozpocet=None, x0=None, sigma0=None,
              sigma_min: float = 1e-12, restart: bool = False):
    n = ev.dim
    koniec = ev.pouzite + _limit(ev, rozpocet)
    d = math.sqrt(n + 1.0)

    def start(x_init):
        if x_init is None:
            x_init = rng.uniform(ev.lower, ev.upper)
        x, fx = ev.hodnot1(x_init)
        return x, fx

    x, fx = start(x0)
    if x is None:
        return
    sigma = 0.2 * float(np.mean(ev.sirka)) if sigma0 is None else float(sigma0)
    while ev.pouzite < koniec and ev.zostava() > 0:
        y, fy = ev.hodnot1(x + sigma * rng.standard_normal(n))
        if y is None:
            break
        uspech = fy <= fx
        if uspech:
            x, fx = y, fy
        sigma *= math.exp(((1.0 if uspech else 0.0) - 0.2) / d)
        sigma = min(sigma, float(np.max(ev.sirka)))
        if sigma < sigma_min:
            if not restart:
                break
            x, fx = start(None)
            if x is None:
                break
            sigma = 0.2 * float(np.mean(ev.sirka))


# ---------------------------------------------------------------------------
# teoria.md, časť 4 – Nelderova–Meadova metóda
#   M = ťažisko n najlepších vrcholov, R = 2M - W, E = 2R - M,
#   C1 = (W + M)/2 (vnútorná kontrakcia), C2 = (M + R)/2 (vonkajšia),
#   zmrštenie X_j <- (B + X_j)/2.
#   variant="standard": štandardná (Lagariasova) logika – expanzia iba ak R je
#       lepší než B, vyhodnotí sa iba jedna z kontrakcií;
#   variant="prednaska": postup z EAL 5 – E sa skúša, keď R je lepší než W,
#       vyhodnotia sa obe kontrakcie C1, C2 a vyberie sa lepšia.
# ---------------------------------------------------------------------------
def nelder_mead(ev: Vyhodnocovac, x0, delta, rozpocet=None, tol: float = 1e-10,
                variant: str = "standard", f0=None):
    """Vráti (najlepší vrchol, jeho hodnota, veľkosť simplexu na konci)."""
    n = ev.dim
    koniec = ev.pouzite + _limit(ev, rozpocet)
    x0 = ev.orez(np.asarray(x0, dtype=float))
    delta = np.broadcast_to(np.asarray(delta, dtype=float), (n,)).copy()

    # počiatočný simplex: x0 a x0 + delta_i e_i (krok smerom dovnútra oblasti)
    S = np.repeat(x0[None, :], n + 1, axis=0)
    for i in range(n):
        krok = delta[i] if x0[i] + delta[i] <= ev.upper[i] else -delta[i]
        S[i + 1, i] += krok
    if f0 is None:
        k = min(n + 1, koniec - ev.pouzite)
        S_e, F = ev.hodnot(S[:k])
        if F.size < n + 1:
            return (S_e[np.argmin(F)], float(F.min()), 0.0) if F.size else (x0, np.inf, 0.0)
        S = S_e
    else:
        k = min(n, koniec - ev.pouzite)
        S_e, F_r = ev.hodnot(S[1:1 + k])
        if F_r.size < n:
            return x0, float(f0), 0.0
        S = np.vstack([x0[None, :], S_e])
        F = np.concatenate([[float(f0)], F_r])

    def jeden(x):
        if ev.pouzite >= koniec:
            return None, None
        return ev.hodnot1(x)

    velkost = np.inf
    while ev.pouzite < koniec and ev.zostava() > 0:
        poradie = np.argsort(F, kind="stable")
        S, F = S[poradie], F[poradie]
        velkost = float(np.max(np.abs(S[1:] - S[0])))
        if velkost < tol:
            break
        B, W = S[0], S[-1]
        fB, fG, fW = F[0], F[-2], F[-1]   # fG = druhý najhorší
        M = S[:-1].mean(axis=0)
        R, fR = jeden(2 * M - W)
        if R is None:
            break

        if variant == "prednaska":
            if fR < fW:
                E, fE = jeden(2 * R - M)
                if E is not None and fE < fR:
                    S[-1], F[-1] = E, fE
                else:
                    S[-1], F[-1] = R, fR
                continue
            C1, fC1 = jeden((W + M) / 2)
            C2, fC2 = jeden((M + R) / 2)
            kand = [(fC, C) for fC, C in ((fC1, C1), (fC2, C2)) if C is not None]
            if kand:
                fC, C = min(kand, key=lambda t: t[0])
                if fC < fW:
                    S[-1], F[-1] = C, fC
                    continue
        else:  # štandardná varianta
            if fB <= fR < fG:
                S[-1], F[-1] = R, fR
                continue
            if fR < fB:
                E, fE = jeden(2 * R - M)
                if E is not None and fE < fR:
                    S[-1], F[-1] = E, fE
                else:
                    S[-1], F[-1] = R, fR
                continue
            if fR < fW:      # vonkajšia kontrakcia C2
                C, fC = jeden((M + R) / 2)
                if C is not None and fC <= fR:
                    S[-1], F[-1] = C, fC
                    continue
            else:            # vnútorná kontrakcia C1
                C, fC = jeden((W + M) / 2)
                if C is not None and fC < fW:
                    S[-1], F[-1] = C, fC
                    continue
        # zmrštenie k najlepšiemu vrcholu
        k = min(n, koniec - ev.pouzite)
        if k <= 0:
            break
        nove = B + 0.5 * (S[1:1 + k] - B)
        S_e, F_e = ev.hodnot(nove)
        S[1:1 + F_e.size], F[1:1 + F_e.size] = S_e, F_e
        if F_e.size < n:
            break

    i = int(np.argmin(F))
    return S[i].copy(), float(F[i]), velkost


# ---------------------------------------------------------------------------
# teoria.md, časti 7.2 a 7.3 – (mu/mu_w, lambda)-CMA-ES; sep=True je
# diagonálna varianta s náročnosťou O(n) na kandidáta.
# ---------------------------------------------------------------------------
def cma_es(ev: Vyhodnocovac, rng, m0, sigma0, rozpocet=None, lam=None,
           sep: bool = False, d0=None, tol_x: float = 1e-12,
           stagnacia_gen=None):
    """Jeden beh CMA-ES. Vráti dôvod ukončenia (reťazec)."""
    n = ev.dim
    koniec = ev.pouzite + _limit(ev, rozpocet)
    lam = int(lam or (4 + int(3 * math.log(n))))
    mu = lam // 2
    w = math.log(mu + 0.5) - np.log(np.arange(1, mu + 1))
    w = w / w.sum()
    mueff = 1.0 / float(np.sum(w ** 2))

    cc = (4 + mueff / n) / (n + 4 + 2 * mueff / n)
    cs = (mueff + 2) / (n + mueff + 5)
    c1 = 2 / ((n + 1.3) ** 2 + mueff)
    cmu = min(1 - c1, 2 * (mueff - 2 + 1 / mueff) / ((n + 2) ** 2 + mueff))
    if sep:  # Ros & Hansen (2008): rýchlejšie učenie diagonály
        c1 = min(1.0, c1 * (n + 2) / 3)
        cmu = min(1 - c1, cmu * (n + 2) / 3)
    ds = 1 + 2 * max(0.0, math.sqrt((mueff - 1) / (n + 1)) - 1) + cs
    chiN = math.sqrt(n) * (1 - 1 / (4 * n) + 1 / (21 * n * n))

    m = ev.orez(np.asarray(m0, dtype=float))
    sigma = float(sigma0)
    D = np.ones(n) if d0 is None else np.asarray(d0, dtype=float).copy()  # smerodajné odchýlky
    if sep:
        c_diag = D ** 2
    else:
        B = np.eye(n)
        C = np.diag(D ** 2)
    ps = np.zeros(n)
    pc = np.zeros(n)
    if stagnacia_gen is None:
        stagnacia_gen = 10 + int(math.ceil(30 * n / lam))
    historia: list[float] = []
    gen = 0

    while True:
        zost = koniec - ev.pouzite
        if zost <= 0 or ev.zostava() <= 0:
            return "rozpocet"
        Z = rng.standard_normal((lam, n))
        Y = Z * D if sep else (Z * D) @ B.T          # y = B D z
        X_e, fy = ev.hodnot(m + sigma * Y)
        if fy.size < lam:
            return "rozpocet"
        Y = (X_e - m) / sigma                        # skutočne vyhodnotené (orezané) body
        gen += 1

        idx = np.argsort(fy, kind="stable")
        Ysel = Y[idx[:mu]]
        yw = w @ Ysel
        m = m + sigma * yw

        # evolučné cesty
        if sep:
            invsqrt_yw = yw / D
        else:
            invsqrt_yw = B @ ((B.T @ yw) / D)
        ps = (1 - cs) * ps + math.sqrt(cs * (2 - cs) * mueff) * invsqrt_yw
        ps_norm = float(np.linalg.norm(ps))
        hsig = ps_norm / math.sqrt(1 - (1 - cs) ** (2 * gen)) / chiN < 1.4 + 2 / (n + 1)
        pc = (1 - cc) * pc + (math.sqrt(cc * (2 - cc) * mueff) * yw if hsig else 0.0)
        dh = (0.0 if hsig else 1.0) * cc * (2 - cc)

        # kovariancia
        if sep:
            c_diag = ((1 - c1 - cmu) * c_diag + c1 * (pc ** 2 + dh * c_diag)
                      + cmu * (w @ (Ysel ** 2)))
            c_diag = np.maximum(c_diag, 1e-300)
            D = np.sqrt(c_diag)
        else:
            C = ((1 - c1 - cmu) * C + c1 * (np.outer(pc, pc) + dh * C)
                 + cmu * (Ysel.T * w) @ Ysel)
            C = 0.5 * (C + C.T)
            vl, B = np.linalg.eigh(C)
            vl = np.maximum(vl, 1e-300)
            D = np.sqrt(vl)

        # veľkosť kroku (CSA)
        sigma *= math.exp(min(1.0, (cs / ds) * (ps_norm / chiN - 1)))
        sigma = min(sigma, 2.0 * float(np.max(ev.sirka)) / float(np.max(D)))

        # ukončovacie podmienky
        historia.append(float(fy[idx[0]]))
        if fy[idx[0]] == fy[idx[min(lam - 1, int(math.ceil(0.7 * lam)))]]:
            sigma *= math.exp(0.2 + cs / ds)   # plochá krajina – zväčšiť krok
        if not np.all(np.isfinite(m)) or not math.isfinite(sigma):
            return "numerika"
        if sigma * float(np.max(D)) < tol_x:
            return "tol_x"
        if float(np.max(D)) / float(np.min(D)) > 1e7:  # kappa(C) > 1e14
            return "podmienenost"
        if len(historia) > stagnacia_gen:
            nedavne = min(historia[-stagnacia_gen:])
            starsie = min(historia[:-stagnacia_gen])
            if nedavne >= starsie - 1e-12 * max(1.0, abs(starsie)):
                return "stagnacia"


def cma_es_ipop(ev: Vyhodnocovac, rng, rozpocet=None, sigma0=None, m0=None,
                sep: bool = False, d0=None, max_restartov: int = 9,
                restart_z: str = "nahodny"):
    """CMA-ES s reštartmi so zdvojnásobením populácie (IPOP)."""
    n = ev.dim
    koniec = ev.pouzite + _limit(ev, rozpocet)
    lam = 4 + int(3 * math.log(n))
    sigma0 = 0.2 * float(np.mean(ev.sirka)) if sigma0 is None else sigma0
    dovody = []
    for r in range(max_restartov + 1):
        if koniec - ev.pouzite < lam:
            break
        if r == 0 and m0 is not None:
            start = m0
        elif restart_z == "best" and ev.best_x is not None:
            start = ev.best_x
        else:
            start = rng.uniform(ev.lower, ev.upper)
        dovod = cma_es(ev, rng, start, sigma0, rozpocet=koniec - ev.pouzite, lam=lam,
                       sep=sep, d0=d0 if r == 0 else None)
        dovody.append(dovod)
        if dovod == "rozpocet":
            break
        lam *= 2
    return dovody


__all__ = ["nahodne_hladanie", "es_1plus1", "nelder_mead", "cma_es", "cma_es_ipop",
           "latinska_hyperkocka"]


# ---------------------------------------------------------------------------
# teoria.md, časť 8 – kvázi-Newtonova metóda BFGS s gradientom
# z konečných diferencií a spätným krokovaním (Armijova podmienka)
#   g_i ≈ (f(x + h e_i) - f(x - h e_i)) / (2h)        (centrálna)
#   d = -V g,   x+ = x + alpha d,   s = x+ - x,  y = g+ - g,  rho = 1/(y^T s)
#   V+ = (I - rho s y^T) V (I - rho y s^T) + rho s s^T
# ---------------------------------------------------------------------------
def gradient_fd(ev, x, fx, h, centralny: bool = True):
    """Odhad gradientu jednou dávkou. Vráti (g, pocet) alebo (None, 0) pri nedostatku rozpočtu."""
    n = ev.dim
    hv = np.full(n, float(h))
    # pri hranici použiť krok smerom dovnútra
    Xp = x + np.diag(hv)
    if centralny:
        Xm = x - np.diag(hv)
        X = np.vstack([Xp, Xm])
    else:
        X = Xp
    if ev.zostava() < X.shape[0]:
        return None
    Xe, y = ev.hodnot(X)
    if y.size < X.shape[0]:
        return None
    if centralny:
        dp = Xe[:n] - x
        dm = Xe[n:] - x
        sp = np.diag(dp)
        sm = np.diag(dm)
        return (y[:n] - y[n:]) / np.where(sp - sm != 0, sp - sm, 1.0)
    sp = np.diag(Xe - x)
    return (y - fx) / np.where(sp != 0, sp, 1.0)


def bfgs_fd(ev: Vyhodnocovac, x0, f0=None, rozpocet=None, h: float = 1e-5,
            centralny: bool = True, max_krokov_ls: int = 30, alpha0: float = 1.0,
            expanzia: bool = False, tol_f: float = 0.0, max_expanzii: int = 6,
            parabola: bool = False):
    """Vráti dôvod ukončenia."""
    n = ev.dim
    koniec = ev.pouzite + _limit(ev, rozpocet)
    x = ev.orez(np.asarray(x0, dtype=float))
    if f0 is None:
        x, fx = ev.hodnot1(x)
        if x is None:
            return "rozpocet"
    else:
        fx = float(f0)
    g = gradient_fd(ev, x, fx, h, centralny)
    if g is None:
        return "rozpocet"
    V = np.eye(n)
    prvy = True
    while ev.pouzite < koniec and ev.zostava() > 0:
        d = -V @ g
        sklon = float(g @ d)
        if sklon >= 0:                      # nie je smer klesania – reset
            V = np.eye(n)
            d = -g
            sklon = float(g @ d)
            if sklon >= 0:
                return "gradient_nulovy"
        if prvy:  # rozumná dĺžka prvého kroku
            alpha = min(1.0, float(np.mean(ev.sirka)) * 0.1 / max(np.linalg.norm(d), 1e-300))
        else:
            alpha = alpha0
        prijate = False
        for _ in range(max_krokov_ls):
            if ev.pouzite >= koniec:
                return "rozpocet"
            xn, fn = ev.hodnot1(x + alpha * d)
            if xn is None:
                return "rozpocet"
            if fn <= fx + 1e-4 * alpha * sklon:
                prijate = True
                break
            alpha *= 0.5
        if not prijate:
            return "line_search"
        if expanzia and alpha >= alpha0:
            # prijatý plný krok: skúsiť dlhší krok, kým sa hodnota zlepšuje
            for _ in range(max_expanzii):
                if ev.pouzite >= koniec:
                    return "rozpocet"
                xe, fe = ev.hodnot1(x + 2 * alpha * d)
                if xe is None:
                    return "rozpocet"
                if fe < fn:
                    xn, fn, alpha = xe, fe, 2 * alpha
                else:
                    break
        if parabola:
            # minimum paraboly cez f(x), sklon v x a f(x + alpha d)
            a2 = (fn - fx - sklon * alpha) / alpha ** 2
            if a2 > 0:
                at = -sklon / (2 * a2)
                if 0.1 * alpha < at < 10 * alpha and abs(at - alpha) > 0.05 * alpha \
                        and ev.pouzite < koniec:
                    xp, fp = ev.hodnot1(x + at * d)
                    if xp is None:
                        return "rozpocet"
                    if fp < fn:
                        xn, fn = xp, fp
        gn = gradient_fd(ev, xn, fn, h, centralny)
        if gn is None:
            return "rozpocet"
        s = xn - x
        yv = gn - g
        ys = float(yv @ s)
        if ys > 1e-12 * float(np.linalg.norm(s) * np.linalg.norm(yv)):
            if prvy:   # škálovanie počiatočnej matice (Nocedal & Wright, vzťah 6.20)
                V = (ys / float(yv @ yv)) * np.eye(n)
            rho = 1.0 / ys
            I = np.eye(n)
            V = (I - rho * np.outer(s, yv)) @ V @ (I - rho * np.outer(yv, s)) + rho * np.outer(s, s)
        prvy = False
        zlepsenie = fx - fn
        x, fx, g = xn, fn, gn
        if float(np.linalg.norm(s)) < 1e-12:
            return "krok_maly"
        if tol_f > 0 and zlepsenie < tol_f * max(1.0, abs(fx)):
            return "tol_f"
    return "rozpocet"
