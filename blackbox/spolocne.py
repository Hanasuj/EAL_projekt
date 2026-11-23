"""Spoločná vrstva pre vyhodnocovanie účelovej funkcie.

Všetky stratégie vyhodnocujú body výhradne cez triedu ``Vyhodnocovac``.
Tá zaručuje technické pravidlá súťaže (pozri docs/analyza_zadania.md, P05–P07, R01–R03):

* každý bod sa pred vyhodnotením oreže do hraníc [lower, upper] a NaN/inf
  sa nahradí stredom oblasti, takže f.batch nikdy nevyhodí ValueError;
* dávka sa oreže na zvyšok rozpočtu, takže nikdy nepríde BudgetExhausted
  (ak by predsa prišla, zachytí sa a nastaví sa príznak ``koniec``);
* vracia skutočne vyhodnotené (orezané) body spolu s hodnotami, aby
  stratégie aktualizovali svoj model podľa toho, čo funkcia naozaj videla.

Najlepší bod si pamätá samotný objekt f (f.best_x, f.best_y).
"""

from __future__ import annotations

import numpy as np
from omm_blackbox import BudgetExhausted


class Vyhodnocovac:
    def __init__(self, f):
        self.f = f
        self.dim = int(f.dim)
        self.lower = np.asarray(f.lower, dtype=float).copy()
        self.upper = np.asarray(f.upper, dtype=float).copy()
        self.sirka = self.upper - self.lower
        self.stred = 0.5 * (self.lower + self.upper)
        self.koniec = False

    # --- rozpočet -----------------------------------------------------------
    def zostava(self) -> int:
        if self.koniec:
            return 0
        return max(0, int(self.f.budget) - int(self.f.evaluations))

    @property
    def pouzite(self) -> int:
        return int(self.f.evaluations)

    @property
    def best_x(self):
        return None if self.f.best_x is None else np.asarray(self.f.best_x, dtype=float)

    @property
    def best_y(self) -> float:
        return float(self.f.best_y)

    # --- vyhodnotenie -------------------------------------------------------
    def orez(self, X) -> np.ndarray:
        """Nahradí nekonečné/NaN zložky stredom oblasti a oreže do hraníc."""
        X = np.array(X, dtype=float)  # kópia
        zle = ~np.isfinite(X)
        if zle.any():
            X[zle] = np.broadcast_to(self.stred, X.shape)[zle]
        return np.clip(X, self.lower, self.upper)

    def hodnot(self, X):
        """Vyhodnotí riadky matice X (k, dim).

        Vráti dvojicu (X_vyhodnotene, y). Ak sa celá dávka nezmestí do
        rozpočtu, vyhodnotí sa iba začiatok dávky; pri vyčerpanom rozpočte
        sa vrátia prázdne polia.
        """
        X = self.orez(np.atleast_2d(X))
        k = min(X.shape[0], self.zostava())
        if k <= 0:
            self.koniec = True
            return X[:0], np.empty(0)
        X = X[:k]
        try:
            y = np.asarray(self.f.batch(X), dtype=float).reshape(-1)
        except BudgetExhausted:
            self.koniec = True
            return X[:0], np.empty(0)
        y = np.where(np.isfinite(y), y, np.inf)
        if self.zostava() <= 0:
            self.koniec = True
        return X, y

    def hodnot1(self, x):
        """Vyhodnotí jeden bod; vráti (x_vyhodnoteny, y) alebo (None, None)."""
        X, y = self.hodnot(np.asarray(x, dtype=float).reshape(1, -1))
        if y.size == 0:
            return None, None
        return X[0], float(y[0])


# --- pomocné funkcie spoločné pre viac stratégií --------------------------------

def latinska_hyperkocka(rng, n_bodov: int, lower, upper) -> np.ndarray:
    """Latinská hyperkocka: v každom z n_bodov intervalov každej osi leží práve jeden bod."""
    dim = len(lower)
    perm = np.argsort(rng.random((n_bodov, dim)), axis=0)  # nezávislá permutácia pre každú os
    U = (perm + rng.random((n_bodov, dim))) / n_bodov
    return lower + U * (upper - lower)


def vyber_vzdialenych(X, y, k: int, d_min: float) -> list[int]:
    """Indexy najviac k najlepších bodov, ktoré sú od seba vzdialené aspoň d_min."""
    poradie = np.argsort(y, kind="stable")
    vybrane: list[int] = []
    for i in poradie:
        if not np.isfinite(y[i]):
            break
        if all(np.linalg.norm(X[i] - X[j]) >= d_min for j in vybrane):
            vybrane.append(int(i))
            if len(vybrane) >= k:
                break
    return vybrane


class Podpriestor:
    """Vyhodnocovač v podpriestore: mení sa iba premenné s indexmi S,
    ostatné ostávajú na hodnotách bodu ``zaklad``. Má rovnaké rozhranie
    ako Vyhodnocovac, takže naň fungujú všetky metódy z metody.py
    (teoria.md, časť 9.4)."""

    def __init__(self, ev: Vyhodnocovac, S, zaklad):
        self.ev = ev
        self.S = np.asarray(S, dtype=int)
        self.zaklad = ev.orez(np.asarray(zaklad, dtype=float))
        self.dim = len(self.S)
        self.lower = ev.lower[self.S]
        self.upper = ev.upper[self.S]
        self.sirka = self.upper - self.lower
        self.stred = 0.5 * (self.lower + self.upper)
        self._best_x = None
        self._best_y = np.inf

    def zostava(self) -> int:
        return self.ev.zostava()

    @property
    def koniec(self):
        return self.ev.koniec

    @property
    def pouzite(self) -> int:
        return self.ev.pouzite

    @property
    def best_x(self):
        return None if self._best_x is None else self._best_x.copy()

    @property
    def best_y(self) -> float:
        return self._best_y

    def plny_bod(self, x_pod):
        x = self.zaklad.copy()
        x[self.S] = x_pod
        return x

    def orez(self, X):
        X = np.array(X, dtype=float)
        zle = ~np.isfinite(X)
        if zle.any():
            X[zle] = np.broadcast_to(self.stred, X.shape)[zle]
        return np.clip(X, self.lower, self.upper)

    def hodnot(self, X):
        X = self.orez(np.atleast_2d(X))
        plne = np.repeat(self.zaklad[None, :], X.shape[0], axis=0)
        plne[:, self.S] = X
        P, y = self.ev.hodnot(plne)
        Xs = P[:, self.S]
        if y.size:
            i = int(np.argmin(y))
            if y[i] < self._best_y:
                self._best_y, self._best_x = float(y[i]), Xs[i].copy()
        return Xs, y

    def hodnot1(self, x):
        X, y = self.hodnot(np.asarray(x, dtype=float).reshape(1, -1))
        if y.size == 0:
            return None, None
        return X[0], float(y[0])
