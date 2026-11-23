"""D03c – f2000: sú slabé premenné kvadratické a separabilné? Pomôže diagonálny Newtonov krok?"""
import numpy as np
from omm_blackbox import Problem
OPT={1:93.33691257655715,2:37.1635093519065,3:27.76889886524485,4:-26.783665871609315,5:-46.297642428567464}
n=2000
def skrin(f,x0,h):
    f0=f(x0); I=np.eye(n); fp=f.batch(np.clip(x0+h*I,-5,5)); fm=f.batch(np.clip(x0-h*I,-5,5))
    return f0,(fp-fm)/(2*h),(fp-2*f0+fm)/h**2,np.maximum(abs(fp-f0),abs(fm-f0))
for seed in [1,2,3]:
    f=Problem("f2000",seed=seed,budget=10**8); rng=np.random.default_rng(seed)
    x0=np.zeros(n); xr=rng.uniform(-3,3,n)
    f0,g1,c1,E=skrin(f,x0,1.0); _,g01,c01,_=skrin(f,x0,0.1); _,gr,cr,_=skrin(f,xr,1.0)
    slabe=np.argsort(E)[:1950]; silne=np.argsort(-E)[:20]
    rel=lambda a,b: np.median(np.abs(a-b)/np.maximum(np.abs(b),1e-12))
    print(f"seed{seed} slabé: median rel. rozdiel c(h=1) vs c(h=0.1) {rel(c1[slabe],c01[slabe]):.3g}; c(stred) vs c(náhodný) {rel(c1[slabe],cr[slabe]):.3g}; c>0: {np.mean(c1[slabe]>0):.3f}")
    print(f"seed{seed} silné: median rel. rozdiel c(h=1) vs c(h=0.1) {rel(c1[silne],c01[silne]):.3g}; c(stred) vs c(náhodný) {rel(c1[silne],cr[silne]):.3g}")
    # diagonalny Newton len na slabych premennych
    x1=x0.copy(); ok=c1>1e-12
    krok=np.where(ok,-g1/np.where(ok,c1,1),0.0)
    x1[slabe]=np.clip(x0[slabe]+krok[slabe],-5,5)
    print(f"seed{seed} f(x0)={f0:.6g}; po Newtonovi na slabých: {f(x1):.6g}; zlepšenie {f0-f(x1):.4g}")
    # Newton na vsetkych
    x2=np.clip(x0+krok,-5,5); print(f"seed{seed} po Newtonovi na všetkých: {f(x2):.6g} (opt {OPT[seed]:.6g})")
    # opakovany Newton
    x=x2.copy()
    for it in range(4):
        fx,g,c,_=skrin(f,x,0.5); ok=c>1e-12; kr=np.where(ok,-g/np.where(ok,c,1),-0.5*np.sign(g))
        best=None
        for t in [0.25,0.5,1.0]:
            xt=np.clip(x+t*kr,-5,5); ft=f(xt)
            if best is None or ft<best[0]: best=(ft,xt)
        if best[0]<fx: x=best[1]
        print(f"   iter{it}: f={min(best[0],fx):.6g}, medzera {min(best[0],fx)-OPT[seed]:.4g}")
