# Black-box súťaž

Riešič spoločnej black-box súťaže. **Vyhodnocuje sa iba `solve.py`**: funkcia
`solve(f, rng_seed)` má nezmenenú signatúru a importuje vlastné pomocné moduly z
tejto zložky priamo (`import metody`, `import strategie`, `from spolocne import …`),
ako to dovoľuje zadanie. Hotové optimalizátory (`scipy.optimize`, `cma`, `optuna` …)
nepoužívame. Riešič používa iba `numpy`, štandardnú knižnicu Pythonu a `omm_blackbox`.

Úplné pravidlá sú na webe projektu (stránka `blackbox.html`). Podrobné odvodenia,
všetky experimenty a priebeh vývoja sú v zložke `docs/`.

| Súbor | Obsah |
|---|---|
| `solve.py` | vstupný bod `solve(f, rng_seed)`; podľa funkcie vyberie stratégiu |
| `strategie.py` | stratégie pre `f2`, `f20` a `f2000` a skríning citlivosti premenných |
| `metody.py` | vlastné implementácie metód: Nelderova–Meadova metóda, BFGS s konečnými diferenciami, $(1+1)$-ES, CMA-ES, náhodné hľadanie |
| `spolocne.py` | `Vyhodnocovac` (orezanie do hraníc, kontrola rozpočtu), latinská hyperkocka, `Podpriestor` |
| `spust_lokalne.py` | skript zo šablóny: beh na verejných vývojových seedoch 1–5 |
| `testy/` | testy zo šablóny (`test_solve.py`, `test_importy.py`) a vlastné testy (`test_vlastne.py`) |
| `vystupy/` | tabuľky a grafy z experimentov |
| `docs/analyza_zadania.md` | rozbor zadania, kontrolný zoznam pravidiel, riziká |
| `docs/teoria.md` | matematické východiská použitých metód |
| `docs/navrh_strategii.md` | návrh stratégií a jeho zmeny počas vývoja |
| `docs/vyvojovy_denik.md` | vývojový denník, kroky K01–K08 |
| `docs/experimenty.md` | záznam všetkých experimentov vrátane neúspešných |

Skripty experimentov sú v zložke `experimenty_blackbox/` v koreni repozitára.
Sú mimo `blackbox/`, pretože používajú `matplotlib`, ktorý `test_importy.py`
v tejto zložke nepovoľuje. Na vyhodnotenie riešiča nie sú potrebné.

Spúšťanie z koreňa repozitára:

```bash
uv sync
uv run pytest blackbox                                # kontroly (30 testov)
uv run python blackbox/spust_lokalne.py               # všetky funkcie, 3 seedy algoritmu
uv run python blackbox/spust_lokalne.py --funkce f20  # iba jedna funkcia
```

Výsledky na vývojových seedoch nie sú hodnotenie. Súťaž sa vyhodnocuje na tajných inštanciách.

## Stratégia

Všetky tri funkcie majú definičný obor $[-5, 5]^n$. Hodnotí sa medzera
$\Delta = f(\mathbf{x}_{\text{best}}) - f^*$ na logaritmickej škále; hodnota pod
$10^{-8}$ sa počíta ako nula a pri zhode rozhoduje menší počet vyhodnotení. Preto pri
každej funkcii najprv hľadáme správne povodie a potom čo najrýchlejšie spresňujeme
riešenie. Voľby vychádzajú z diagnostiky funkcií (D01–D04 v `docs/experimenty.md`),
nie z predpokladov o ich vzorci.

Spoločné pravidlá platia pre všetky stratégie. Každý bod sa pred vyhodnotením oreže do
hraníc. Veľkosť dávky sa skráti na zvyšok rozpočtu. Všetka náhodnosť pochádza z
`np.random.default_rng(rng_seed)`. O priebehu sa rozhoduje iba podľa počtu
vyhodnotení, nikdy podľa času. Vracia sa `f.best_x`, teda skutočne vyhodnotený bod.
Ak stratégia skončí skôr, zvyšok rozpočtu spresňuje okolie najlepšieho bodu metóda
$(1+1)$-ES. Chyba v stratégii nezhodí beh: vrátime doteraz najlepší bod.

### `f2` (rozpočet 300)

Diagnostika ukázala 29 až 56 lokálnych miním a jedno hlboké, úzke, natočené údolie.

1. **Prieskum:** 40 % rozpočtu (120 bodov) rozmiestnime latinskou hyperkockou.
2. **Výber štartov:** z najlepších bodov vyberieme 5, ktoré sú navzájom vzdialené aspoň
   $d_{\min} = \bar{w} / n_0^{1/n}$, kde $\bar{w}$ je priemerná šírka intervalu,
   $n_0$ počet bodov prieskumu a $n = 2$ rozmer. Je to typická vzdialenosť medzi bodmi
   rovnomernej vzorky, takže štarty neležia v tom istom povodí.
3. **Krátke lokálne behy:** z každého štartu 15 vyhodnotení Nelderovej–Meadovej metódy.
4. **Dokončenie:** zvyšok rozpočtu dostane najlepší kandidát. Po konvergencii sa
   simplex reštartuje; ak reštart už nič nezlepší, pokračuje ďalší kandidát.

### `f20` (rozpočet 4 000)

Funkcia je hladká a natočená. Podmienenosť Hessovej matice pri optime je približne
$\kappa \approx 190$ až $1160$. Funkcia má aj lokálne minimá.

Používame kvázi-Newtonovu metódu **BFGS** s gradientom z dopredných diferencií
$$
g_i \approx \frac{f(\mathbf{x} + h\,\mathbf{e}_i) - f(\mathbf{x})}{h}, \qquad h = 10^{-7},
$$
ktorý stojí $n = 20$ vyhodnotení. Inverzná Hessova matica $\mathbf{V}_k$ sa aktualizuje
vzťahom
$$
\mathbf{V}_{k+1} = \left(\mathbf{I} - \rho\,\mathbf{s}\mathbf{y}^\top\right)\mathbf{V}_k\left(\mathbf{I} - \rho\,\mathbf{y}\mathbf{s}^\top\right) + \rho\,\mathbf{s}\mathbf{s}^\top,
\qquad \rho = \frac{1}{\mathbf{y}^\top\mathbf{s}},
$$
kde $\mathbf{s}$ je posledný krok a $\mathbf{y}$ zmena gradientu. Metóda sa tak postupne
naučí zakrivenie funkcie a natočenie nevadí. Krok hľadá Armijovo pravidlo s
predĺžením kroku a parabolickou interpoláciou. Štart je najlepší z 50 bodov latinskej
hyperkocky. Po konvergencii sa beh opakuje z nového štartu (multištart), aby sme
unikli z lokálneho minima.

### `f2000` (rozpočet 20 000)

Diagnostika (D03, D04) ukázala, že na hodnote výrazne záleží iba približne 9 až 18
premenných a tie spolu interagujú. Ostatné premenné majú malý, takmer separabilný a
lokálne kvadratický vplyv.

1. **Skríning:** zo stredu oblasti vyhodnotíme $f(\mathbf{x}_0 \pm h\,\mathbf{e}_i)$
   pre všetky $i$ s $h = 2$ (spolu $2n + 1 = 4001$ vyhodnotení). Efekt premennej je
   $E_i = \max\left(|f_+ - f_0|,\ |f_- - f_0|\right)$.
   Do podpriestoru vyberieme $k$ premenných s $E_i > 10^{-3}\max_j E_j$, kde
   $k$ obmedzíme na interval $[10, 40]$.
2. **Slabé premenné:** z tých istých hodnôt odhadneme prvú a druhú deriváciu
   $g_i = (f_+ - f_-)/(2h)$, $c_i = (f_+ - 2f_0 + f_-)/h^2$ a urobíme jeden
   diagonálny Newtonov krok $x_i \leftarrow x_i - g_i / c_i$ (len pre $c_i > 0$).
   Nový bod prijmeme, iba ak je lepší.
3. **Silné premenné:** zvyšok rozpočtu použije BFGS v podpriestore $k$ silných
   premenných, rovnaká metóda ako pri `f20`, s multištartom.

## Experimenty

Rozhodnutia sme robili iba na vývojových seedoch inštancií 1–5 so známym $f^*$
a vždy 10 seedmi algoritmu (50 behov na funkciu). Pri `f2` a `f20` sme ich overili aj
na seedoch 6–25. Podrobnosti a všetky neúspešné pokusy sú v `docs/experimenty.md`.

**Porovnanie s referenciami (E01–E03, verzia po etape 4):**

| Funkcia | náhodné hľadanie | $(1+1)$-ES | náš riešič |
|---|---:|---:|---:|
| `f2` – medián medzery | 1,31 | 3,40 | $7 \cdot 10^{-14}$ |
| `f20` – medián medzery | 16 800 | 120 | $1{,}5 \cdot 10^{-9}$ |
| `f2000` – medián medzery | 740 | 14,6 | 1,57 |

**Zlepšenie v etapách 5–6 (E03 → E40, rovnaké inštancie a seedy):**

| Funkcia | E03 | E40 (súčasná verzia) |
|---|---|---|
| `f2` | 94 % behov pod $10^{-8}$, optimum v priemere po 263 vyhodnoteniach | 98 % (seedy 6–25: 99 %), po 247 vyhodnoteniach |
| `f20` | 100 % pod $10^{-8}$, po 2 738 vyhodnoteniach | 100 % (seedy 6–25: 96 %), po 1 675 vyhodnoteniach |
| `f2000` | medián medzery 1,57, najhorší beh 17,1 | medián 0,339, najhorší beh 5,88 |

Najdlhší beh trvá 0,9 s (`f2000`), limity sú 30, 60 a 120 s.

**Hlavné zistenie:** Pôvodný návrh počítal pre `f20` a podpriestor `f2000` s metódou
CMA-ES, ktorá je odolná voči natočeniu a zlej podmienenosti. Pri hladkých funkciách
a malom rozpočte však bola BFGS s gradientom z konečných diferencií výrazne lepšia.
Pri `f20` dosiahla CMA-ES medián medzery približne 20, kým BFGS bola pod $10^{-8}$ (E21).

**Neúspešné pokusy** (zapísané v `docs/experimenty.md`): CMA-ES pre `f20` (E21),
centrálne diferencie a iné kroky $h$ (E21b), krátke paralelné štarty pre `f20` (E23),
druhé kolo Newtonovho kroku na slabých premenných `f2000` (E30).

**Kde riešič zlyháva:**

- `f2`: približne 1 až 2 % behov nenájde globálne údolie a skončí v lokálnom minime
  (najhorší beh 3,4).
- `f20`: približne 4 % behov na validačných inštanciách skončí v lokálnom minime a
  ďalší štart sa už nestihne dokonvergovať.
- `f2000`: medzera približne 0,3 je ďaleko od nuly. Asi 0,2 pochádza zo slabých
  premenných, kde jeden Newtonov krok nestačí, zvyšok z multimodality silných premenných.
  Pri niektorých inštanciách (seed 5) zostane beh v horšom povodí s medzerou 5,9.
- Všetky merania sú z Linuxu (Python 3.13, numpy 2.5; overené aj Python 3.11 s numpy 2.0),
  nie z vyhodnocovacieho prostredia.
