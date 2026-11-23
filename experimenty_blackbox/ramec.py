"""Spoločný rámec experimentov: referenčné hodnoty, behy variantov, ukazovatele."""
import json, sys, time
from pathlib import Path
import numpy as np
KOREN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOREN / "blackbox"))
from omm_blackbox import Problem  # noqa: E402

ROZPOCET = {"f2": 300, "f20": 4000, "f2000": 20000}
OPT = {('f2', 1): 5.024291116290591, ('f2', 2): -1.2133799561780165, ('f2', 3): 12.83110210731278,
       ('f2', 4): -3.101878057321116, ('f2', 5): -3.8790829711275236, ('f20', 1): 4.404178732675476,
       ('f20', 2): 28.767353524649977, ('f20', 3): 11.301712624462269, ('f20', 4): 2.3548290874466176,
       ('f20', 5): 35.409347441170766, ('f2000', 1): 93.33691257655715, ('f2000', 2): 37.1635093519065,
       ('f2000', 3): 27.76889886524485, ('f2000', 4): -26.783665871609315, ('f2000', 5): -46.297642428567464}
REF_SUBOR = Path(__file__).resolve().parent / "referencie.json"

def nacitaj_ref():
    ref = {f"{k[0]}:{k[1]}": v for k, v in OPT.items()}
    if REF_SUBOR.exists():
        for k, v in json.loads(REF_SUBOR.read_text()).items():
            if k not in ref:
                ref[k] = v
    return ref

def uloz_ref(nove):
    stare = json.loads(REF_SUBOR.read_text()) if REF_SUBOR.exists() else {}
    for k, v in nove.items():
        if k.split(":")[0] + ":" + k.split(":")[1] in {f"{a}:{b}" for a, b in OPT}:
            continue
        stare[k] = min(v, stare.get(k, np.inf))
    REF_SUBOR.write_text(json.dumps(stare, indent=1, sort_keys=True))

class Zaznam:
    def __init__(s, f): s._f = f; s.y = []
    def __getattr__(s, a): return getattr(s._f, a)
    def __call__(s, x): v = s._f(x); s.y.append(float(v)); return v
    def batch(s, X): v = s._f.batch(X); s.y.extend(np.atleast_1d(v).tolist()); return v

def beh(fn, seed, rng_seed, varianta, rozpocet=None):
    f = Zaznam(Problem(fn, seed=seed, budget=rozpocet or ROZPOCET[fn]))
    t = time.perf_counter(); varianta(f, rng_seed); cas = time.perf_counter() - t
    return np.minimum.accumulate(np.array(f.y)), cas

def vyhodnot(fn, varianta, seedy, rng_seedy, ref=None, nazov="", vypis=True):
    ref = ref or nacitaj_ref()
    g, hits, casy, nove = [], [], [], {}
    for s in seedy:
        r_s = ref.get(f"{fn}:{s}")
        for r in rng_seedy:
            krivka, cas = beh(fn, s, r, varianta)
            nove[f"{fn}:{s}"] = min(nove.get(f"{fn}:{s}", np.inf), float(krivka[-1]))
            if r_s is None:
                continue
            b = krivka - r_s
            g.append(max(b[-1], 0.0)); casy.append(cas)
            hits.append(int(np.argmax(b < 1e-8) + 1) if (b < 1e-8).any() else np.nan)
    uloz_ref(nove)
    g = np.array(g); L = np.log10(np.maximum(g, 1e-8))
    vys = dict(nazov=nazov, median=float(np.median(g)), najhorsi=float(g.max()), log_med=float(np.median(L)),
               log_priemer=float(L.mean()), uspech=float(np.mean(g < 1e-8)),
               hit_med=float(np.nanmedian(hits)) if np.isfinite(hits).any() else np.nan,
               cas_max=float(max(casy)), n=len(g))
    if vypis:
        print(f"{fn:5s} {nazov:40s} med {vys['median']:9.3g} | najhorší {vys['najhorsi']:9.3g} | "
              f"priem.log10 {vys['log_priemer']:6.2f} | <1e-8 {vys['uspech']:4.0%} | "
              f"vyhodn. do 1e-8 {vys['hit_med']:6.0f} | čas {vys['cas_max']:.2f}s | n={vys['n']}", flush=True)
    return vys
