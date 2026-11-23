"""D04 – f2000: z čoho sa skladá zvyšková medzera po solve (slabé vs. silné premenné)."""
import numpy as np
from ramec import Problem, OPT
from spolocne import Vyhodnocovac, Podpriestor
import strategie, metody
n=2000
for s in [1,2,3,4,5]:
    f=Problem("f2000",seed=s,budget=20000); ev=Vyhodnocovac(f); strategie.strategia_f2000(ev,np.random.default_rng(0))
    xb=f.best_x.copy(); g0=f.best_y-OPT[("f2000",s)]
    # identifikácia silných z nového skríningu zo stredu (veľký rozpočet)
    F=Problem("f2000",seed=s,budget=10**7); E=Vyhodnocovac(F)
    f0,g,c,Ef=strategie.skrining(E,np.zeros(n),2.0); S=np.sort(np.argsort(-Ef)[:20]); W=np.setdiff1d(np.arange(n),S)
    # 1) iterovaný Newton iba na slabých z xb
    x=xb.copy()
    for it in range(5):
        fx=F.batch(x[None])[0]; h=0.3
        X=np.repeat(x[None],len(W),0); X[np.arange(len(W)),W]+=h; fp=F.batch(np.clip(X,-5,5))
        X=np.repeat(x[None],len(W),0); X[np.arange(len(W)),W]-=h; fm=F.batch(np.clip(X,-5,5))
        gg=(fp-fm)/(2*h); cc=(fp-2*fx+fm)/h**2; x2=x.copy(); ok=cc>1e-12; x2[W]=np.clip(x[W]+np.where(ok,-gg/np.where(ok,cc,1),0),-5,5)
        if F.batch(x2[None])[0]<fx: x=x2
    gw=F.batch(x[None])[0]-OPT[("f2000",s)]
    # 2) potom dlhá CMA na silných
    P=Podpriestor(E,S,x); metody.cma_es_ipop(P,np.random.default_rng(1),m0=x[S],sigma0=0.5,rozpocet=100000,restart_z="best")
    print(f"seed{s}: medzera po solve {g0:.4g}; po 5 kolách Newtona na slabých {gw:.4g}; po dlhej CMA na silných {P.best_y-OPT[('f2000',s)]:.4g}",flush=True)
