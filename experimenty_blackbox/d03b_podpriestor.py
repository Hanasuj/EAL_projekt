"""D03b – f2000: koľko medzery vysvetlia dôležité premenné (veľký rozpočet, len diagnostika)."""
import sys, numpy as np
sys.path.insert(0,"blackbox")
from omm_blackbox import Problem
from spolocne import Vyhodnocovac
import metody
OPT={1:93.33691257655715,2:37.1635093519065,3:27.76889886524485,4:-26.783665871609315,5:-46.297642428567464}
n=2000
class Pod:  # obal: optimalizacia len v podmnozine S, ostatne fixne
    def __init__(s,f,S,base): s.f=f;s.S=S;s.base=base.copy();s.dim=len(S);s.lower=f.lower[S];s.upper=f.upper[S];s.budget=10**7;s.best_x=None;s.best_y=np.inf
    @property
    def evaluations(s): return s.f.evaluations
    def batch(s,X):
        Z=np.repeat(s.base[None],len(X),0); Z[:,s.S]=X; y=s.f.batch(Z)
        i=np.argmin(y)
        if y[i]<s.best_y: s.best_y=y[i]; s.best_x=X[i].copy()
        return y
for seed in [1,2,3,4,5]:
    f=Problem("f2000",seed=seed,budget=10**8); x0=np.zeros(n); h=1.0
    f0=f(x0); I=np.eye(n); fp=f.batch(x0+h*I); fm=f.batch(x0-h*I)
    E=np.maximum(np.abs(fp-f0),np.abs(fm-f0)); srt=np.argsort(-E)
    for k in [10,20,40]:
        S=np.sort(srt[:k]); P=Pod(f,S,x0); ev=Vyhodnocovac(P)
        metody.cma_es_ipop(ev,np.random.default_rng(0),rozpocet=30000,sigma0=2.0,restart_z="best")
        xb=x0.copy(); xb[S]=P.best_x
        print(f"seed{seed} k={k}: f(best v podpriestore)={P.best_y:.6g}, medzera={P.best_y-OPT[seed]:.4g}")
    # potom vsetky premenne: (1+1)-ES zo xb s velkym rozpoctom
    f2=Problem("f2000",seed=seed,budget=200000); ev=Vyhodnocovac(f2)
    metody.es_1plus1(ev,np.random.default_rng(1),x0=xb,sigma0=0.05,rozpocet=200000)
    print(f"seed{seed}: po 200k (1+1)-ES vo všetkých premenných z najlepšieho k=40: medzera={f2.best_y-OPT[seed]:.4g}")
