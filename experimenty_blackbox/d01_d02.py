"""D01 – mapa f2 (mriežka 200x200); D02 – Hessián f20 v okolí dobrého bodu."""
import sys, numpy as np
sys.path.insert(0,"blackbox")
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from omm_blackbox import Problem
from spolocne import Vyhodnocovac
import metody
OPT2={1:5.024291116290591,2:-1.2133799561780165,3:12.83110210731278,4:-3.101878057321116,5:-3.8790829711275236}
fig,ax=plt.subplots(1,5,figsize=(25,5))
for s in range(1,6):
    f=Problem("f2",seed=s,budget=10**6); g=np.linspace(-5,5,201); X,Y=np.meshgrid(g,g)
    Z=f.batch(np.c_[X.ravel(),Y.ravel()]).reshape(X.shape)
    # pocet lokalnych minim na mriezke (8-susedstvo)
    from numpy.lib.stride_tricks import sliding_window_view as sw
    P=np.pad(Z,1,constant_values=np.inf); W=sw(P,(3,3)); loc=(Z<=W.min(axis=(2,3)))
    i=np.unravel_index(np.argmin(Z),Z.shape)
    print(f"f2 seed{s}: min mriežky {Z.min():.5g} v ({X[i]:.2f},{Y[i]:.2f}), opt {OPT2[s]:.5g}; lokálnych miním na mriežke {loc.sum()}; rozsah {Z.min():.3g}..{Z.max():.3g}")
    ax[s-1].contourf(X,Y,Z,40); ax[s-1].plot(X[i],Y[i],'r*',ms=12); ax[s-1].set_title(f"f2 seed {s}")
fig.tight_layout(); fig.savefig("blackbox/vystupy/d01_krajina_f2.png",dpi=80)
# D02
for s in [1,2,3]:
    f=Problem("f20",seed=s,budget=10**6); ev=Vyhodnocovac(f)
    metody.cma_es_ipop(ev,np.random.default_rng(0),rozpocet=60000,restart_z="best")
    x=f.best_x.copy(); n=20; h=1e-3; f0=f(x); H=np.zeros((n,n)); I=np.eye(n)
    for i in range(n):
        for j in range(i,n):
            H[i,j]=H[j,i]=(f(x+h*I[i]+h*I[j])-f(x+h*I[i]-h*I[j])-f(x-h*I[i]+h*I[j])+f(x-h*I[i]-h*I[j]))/(4*h*h)
    vl,V=np.linalg.eigh(H)
    os_zarovnanie=np.max(np.abs(V),axis=0)  # 1 = vlastny vektor rovnobezny s osou
    print(f"f20 seed{s}: best po 60k CMA {f.best_y:.10g}; vlastné čísla H: min {vl.min():.3g}, max {vl.max():.3g}, kappa {vl.max()/max(vl.min(),1e-300):.3g}; max|zložka| vl. vektorov median {np.median(os_zarovnanie):.2f}")
    # hladkost: diferencie pre rozne h
    for hh in [1e-1,1e-2,1e-4]:
        d2=(f(x+hh*I[0])-2*f0+f(x-hh*I[0]))/hh**2
        print(f"   h={hh}: d2f/dx1^2 = {d2:.6g} (H11 pri h=1e-3: {H[0,0]:.6g})")
