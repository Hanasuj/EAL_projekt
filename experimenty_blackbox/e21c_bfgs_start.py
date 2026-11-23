import sys, numpy as np
sys.path.insert(0,"blackbox")
from omm_blackbox import Problem
from spolocne import Vyhodnocovac, latinska_hyperkocka
import metody
def strat(ev,rng,n_init):
    first=True
    while ev.zostava()>0:
        if n_init>0:
            X,y=ev.hodnot(latinska_hyperkocka(rng,min(n_init,ev.zostava()),ev.lower,ev.upper))
            if y.size==0: break
            x0=X[np.argmin(y)]; f0=y.min()
        else:
            x0,f0=ev.hodnot1(rng.uniform(ev.lower,ev.upper))
            if x0 is None: break
        r=metody.bfgs_fd(ev,x0,f0=f0,h=1e-7,centralny=False)
        if r=="rozpocet": break
# referencie
refs={}
for s in range(1,26):
    f=Problem("f20",seed=s,budget=400000); ev=Vyhodnocovac(f); strat(ev,np.random.default_rng(7),50); refs[s]=f.best_y
for n_init in [0,20,50,200]:
    g=[];hits=[]
    for s in range(1,26):
        for r in range(4):
            f=Problem("f20",seed=s,budget=4000); rec=[]
            class W:
                def __getattr__(sf,a): return getattr(f,a)
                def batch(sf,X):
                    y=f.batch(X); rec.extend(y); return y
            ev=Vyhodnocovac(W()); strat(ev,np.random.default_rng(r),n_init)
            b=np.minimum.accumulate(rec)-refs[s]; g.append(b[-1]); hits.append(np.argmax(b<1e-8)+1 if (b<1e-8).any() else np.nan)
    g=np.array(g); print(f"n_init={n_init}: podiel <1e-8 {np.mean(g<1e-8):.2f}, najhorší {g.max():.3g}, medián vyhodn. do <1e-8 {np.nanmedian(hits):.0f}, 90% kvantil {np.nanquantile(hits,0.9):.0f}")
