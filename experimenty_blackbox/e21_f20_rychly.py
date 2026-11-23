import sys, time, numpy as np
sys.path.insert(0,"blackbox")
from omm_blackbox import Problem
from spolocne import Vyhodnocovac, latinska_hyperkocka
import metody, strategie
OPT={1:4.404178732675476,2:28.767353524649977,3:11.301712624462269,4:2.3548290874466176,5:35.409347441170766}
def bfgs_strat(ev,rng,h=1e-5,c=True):
    while ev.zostava()>0:
        x0=ev.best_x if ev.best_x is not None else rng.uniform(ev.lower,ev.upper)
        r=metody.bfgs_fd(ev,x0,h=h,centralny=c)
        if r=="rozpocet": break
VAR={
 "(1+1)-ES": lambda ev,rng: metody.es_1plus1(ev,rng),
 "CMA ipop best": lambda ev,rng: strategie.strategia_f20(ev,rng),
 "CMA ipop nahodny": lambda ev,rng: strategie.strategia_f20(ev,rng,restart_z="nahodny"),
 "CMA bez restartu": lambda ev,rng: metody.cma_es(ev,rng,np.zeros(20),2.0,stagnacia_gen=10**9),
 "BFGS central h1e-5": lambda ev,rng: bfgs_strat(ev,rng),
 "BFGS dopredny h1e-7": lambda ev,rng: bfgs_strat(ev,rng,1e-7,False),
}
for nm,fn in VAR.items():
    gaps=[]
    for s in range(1,6):
        for r in range(3):
            f=Problem("f20",seed=s,budget=4000); ev=Vyhodnocovac(f); fn(ev,np.random.default_rng(r)); gaps.append(max(f.best_y-OPT[s],1e-12))
    L=np.log10(gaps); print(f"{nm:22s} median gap {np.median(gaps):.3g}  worst {max(gaps):.3g}  log10 med {np.median(L):.2f}")
