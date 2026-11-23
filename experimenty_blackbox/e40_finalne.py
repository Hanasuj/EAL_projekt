"""E40 – porovnanie verzie etapy 4 (E03) a verzie po etape 6 (E40) na rovnakých behoch."""
import numpy as np
from ramec import vyhodnot
import solve as S
var = lambda f, r: S.solve(f, r)
for fn, seedy, rng in [("f2", range(1, 6), range(10)), ("f20", range(1, 6), range(10)), ("f2000", range(1, 6), range(10)),
                       ("f2", range(6, 26), range(10)), ("f20", range(6, 26), range(5)), ("f2000", range(6, 16), range(3))]:
    vyhodnot(fn, var, seedy, rng, nazov=f"E40 solve.py, inštancie {seedy.start}–{seedy.stop - 1}")
