"""D03 – diagnostika f2000: citlivosť premenných a separabilita (mimo súťažného rozpočtu)."""
import numpy as np
from omm_blackbox import Problem
n=2000
for seed in [1,2,3]:
    f=Problem("f2000",seed=seed,budget=10**7)
    rng=np.random.default_rng(100+seed)
    out=[]
    for zakl,x0 in [("stred",np.zeros(n)),("nahodny",rng.uniform(-4,4,n))]:
        for h in [0.1,1.0]:
            f0=f(x0); I=np.eye(n)
            fp=f.batch(np.clip(x0+h*I,-5,5)); fm=f.batch(np.clip(x0-h*I,-5,5))
            g=(fp-fm)/(2*h); c=(fp-2*f0+fm)/h**2
            E=np.maximum(np.abs(fp-f0),np.abs(fm-f0))
            q=np.quantile(E,[0,0.5,0.9,0.99,1])
            srt=np.sort(E)[::-1]
            print(f"seed{seed} {zakl} h={h} f0={f0:.4g} |E| kvantily 0/50/90/99/100%: {np.array2string(q,precision=3)}; top10={np.array2string(srt[:10],precision=3)}; #E>1%max={np.sum(E>0.01*srt[0])} #E>1e-9={np.sum(E>1e-9)} c<0:{np.sum(c<-1e-9)}")
            out.append((zakl,h,E))
    # stabilita poradia: prekryv top-50 medzi stred h=1 a nahodny h=1
    Ea=out[1][2]; Eb=out[3][2]
    ta=set(np.argsort(-Ea)[:50]); tb=set(np.argsort(-Eb)[:50])
    print(f"seed{seed} prekryv top50 stred/nahodny: {len(ta&tb)}")
    # aditivita na vzorke dvojic
    x0=rng.uniform(-4,4,n); h=1.0; f0=f(x0)
    imp=np.argsort(-Eb)[:20]; neimp=np.argsort(Eb)[:20]
    for nazov,pool in [("dolezite",imp),("nedolezite",neimp),("zmes",np.r_[imp[:10],neimp[:10]])]:
        Is=[]
        for _ in range(30):
            i,j=rng.choice(pool,2,replace=False)
            ei=np.zeros(n);ei[i]=h; ej=np.zeros(n); ej[j]=h
            vals=f.batch(np.clip(np.stack([x0+ei+ej,x0+ei,x0+ej]),-5,5))
            I=vals[0]-vals[1]-vals[2]+f0
            Is.append(abs(I)/max(abs(vals[1]-f0),abs(vals[2]-f0),1e-12))
        print(f"seed{seed} aditivita {nazov}: median |I|/max|efekt| = {np.median(Is):.3g}, max {np.max(Is):.3g}")
