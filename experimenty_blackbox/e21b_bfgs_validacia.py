import sys, numpy as np
sys.path.insert(0,"blackbox")
from omm_blackbox import Problem
from spolocne import Vyhodnocovac
import metody
def bfgs_strat(ev,rng,h=1e-7,c=False):
    while ev.zostava()>0:
        x0=ev.best_x if ev.best_x is not None else rng.uniform(ev.lower,ev.upper)
        r=metody.bfgs_fd(ev,x0,h=h,centralny=c)
        if r=="rozpocet": break
res=[]
for s in range(6,26):
    # referencia: dlhy beh BFGS + CMA
    f=Problem("f20",seed=s,budget=200000); ev=Vyhodnocovac(f)
    bfgs_strat(ev,np.random.default_rng(99)); ref=f.best_y
    f=Problem("f20",seed=s,budget=60000); ev=Vyhodnocovac(f); metody.cma_es_ipop(ev,np.random.default_rng(98),restart_z="best"); ref=min(ref,f.best_y)
    for h in [1e-7,1e-6,1e-8]:
      for r in range(3):
        f=Problem("f20",seed=s,budget=4000)
        rec=[]
        class W:
            def __getattr__(sf,a): return getattr(f,a)
            def batch(sf,X):
                y=f.batch(X); rec.extend(y); return y
        ev=Vyhodnocovac(W()); bfgs_strat(ev,np.random.default_rng(r),h=h)
        b=np.minimum.accumulate(rec); hit=np.argmax(b-ref<1e-8)+1 if np.any(b-ref<1e-8) else -1
        res.append((s,h,r,f.best_y-ref,hit))
import collections
for x in res:
    if x[3]>1e-8: print("zlyhanie",x)
for h in [1e-7,1e-6,1e-8]:
    g=np.array([x[3] for x in res if x[1]==h]); hits=[x[4] for x in res if x[1]==h]
    print(f"h={h}: medián medzery (odhad) {np.median(g):.3g}, najhorší {g.max():.3g}, podiel <1e-8: {np.mean(g<1e-8):.2f}, medián vyhodnotení do <1e-8: {np.median([x for x in hits if x>0]) if any(x>0 for x in hits) else '-'}")
