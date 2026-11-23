# Etapa 3 – Návrh stratégií pre `f2`, `f20` a `f2000`

Tento dokument navrhuje konkrétne postupy pre každú funkciu, delenie rozpočtu
a architektúru kódu. **Nič z toho ešte nie je implementované ani overené.**
Všetky očakávania sú hypotézy **[H]**, ktoré overia experimenty z
`analyza_zadania.md` (časť 6). Teória k metódam je v `teoria.md`.

Pri každom rozhodnutí postupujeme podľa dohodnutej schémy: problém → možnosti
→ porovnanie → odporúčanie → dôvod.

---

## 1. Spoločná architektúra solvera

### 1.1 Problém

Každá stratégia musí dodržať rovnaké technické pravidlá (orezanie do hraníc,
neprekročenie rozpočtu, reprodukovateľnosť, návrat `f.best_x`). Ak by to
riešila každá stratégia sama, rastie riziko neplatného behu (R01–R03, R11).

### 1.2 Odporúčanie

Jedna spoločná vrstva pre vyhodnocovanie a jednoduché vetvenie v `solve`:

```
blackbox/
  solve.py           solve(f, rng_seed) – iba vetvenie podľa f.name
  spolocne.py        Vyhodnocovac: orezanie, kontrola rozpočtu, dávky, história
  strategia_f2.py    prieskum + lokálne spresnenie
  strategia_f20.py   CMA-ES (prípadne BFGS)
  strategia_f2000.py skríning + podpriestor / sep-ES (podľa D03)
  docs/              dokumentácia
```

Experimentálne a grafové skripty budú **mimo** `blackbox/` (napr. v
`experimenty_blackbox/` v koreni repozitára), pretože `test_importy.py`
kontroluje každý `.py` súbor v `blackbox/` a `matplotlib`/`pandas` by test
zhodili (R06).

**Vyhodnocovač (`spolocne.py`) – zodpovednosti:**

1. `zostava()` = `f.budget - f.evaluations`.
2. `hodnot(X)`: oreže body `np.clip(X, lower, upper)`, nahradí prípadné
   `NaN` (náhradný bod = aktuálne najlepší), oreže dávku na `zostava()`,
   zavolá `f.batch`, vráti hodnoty **a skutočne vyhodnotené (orezané) body**.
   Výnimku `BudgetExhausted` zachytí a nastaví príznak „koniec“.
3. Ak je rozpočet 0, vráti prázdny výsledok (stratégia sa ukončí sama).

**`solve`:**

```python
def solve(f, rng_seed: int) -> np.ndarray:
    rng = np.random.default_rng(rng_seed)
    ev = Vyhodnocovac(f)
    try:
        if f.name == "f2":    strategia_f2(ev, rng)
        elif f.name == "f20": strategia_f20(ev, rng)
        else:                 strategia_f2000(ev, rng)   # aj neznámy názov
        doplnenie_rozpoctu(ev, rng)  # ak zostali vyhodnotenia, lokálne okolo best
    except Exception:
        # posledná poistka: ak sa niečo pokazí, beh nesmie spadnúť
        if f.best_x is None:
            ev.hodnot(stred_oblasti)
    return np.asarray(f.best_x)
```

Poistka `except Exception` je zámerná: neplatný beh = posledné miesto, kým
akýkoľvek vyhodnotený bod je lepší **[Z]**. Pri vývoji ju budeme mať vypnutú
(prepínač), aby sa chyby neskryli.

### 1.3 Ďalšie spoločné zásady

- **Reprodukovateľnosť:** jediný generátor `rng` z `rng_seed`; ak treba viac
  nezávislých prúdov, `np.random.SeedSequence(rng_seed).spawn(k)` (dlho
  existujúce API, R09). Žiadne rozhodnutia podľa času (R05).
- **Rozpočet v podieloch:** všetky fázy sa počítajú z `f.budget`, nie z
  konštánt, a každá fáza má minimum, pod ktorým sa preskočí (R07, P14).
- **Rozmer z `f.dim`,** nie z názvu (ak by sa názov líšil).

---

## 2. Stratégia pre `f2` (2D, 300 vyhodnotení, veľa lokálnych miním)

### 2.1 Problém

Musíme trafiť povodie globálneho minima a v ňom sa dostať na $\Delta < 10^{-8}$,
a to čo najskôr (pri zhode rozhoduje počet vyhodnotení **[Z]**).

### 2.2 Možnosti

| Varianta | Opis | Pre | Proti |
|---|---|---|---|
| A | LHS/mriežka → výber $k$ vzdialených najlepších bodov → Nelder–Mead z každého → dokončenie najlepšieho | jasné oddelenie prieskumu a spresnenia; ľahko obhájiteľné | treba nastaviť $N_0$, $k$, rozpočty |
| B | CRS z prednášky (populácia + odrazy) | jedna metóda, prirodzene globálna | pomalšie záverečné spresnenie [teória, časť 5] |
| C | Postupné zjemňovanie mriežky („zoom“) okolo najlepších buniek | deterministické | riziko, že prvá mriežka minie úzke povodie |
| D | Multištart $(1+1)$-ES | jednoduché | ES v 2D spresňuje pomalšie ako Nelder–Mead [H] |

### 2.3 Odporúčanie: varianta A, varianta B ako konkurent v E11

**Fázy (počiatočné hodnoty, budú sa ladiť v E10/E11):**

1. **Prieskum:** $N_0 \approx 0{,}4B = 120$ bodov latinskej hyperkocky
   (jedna dávka). Pozn.: pred finálnym rozhodnutím o $N_0$ urobíme diagnostiku
   D01 (mapa krajiny), aby sme odhadli veľkosť povodí.
2. **Výber štartov:** zoradiť body, zobrať najviac $k = 4$ najlepšie, ktoré sú
   od seba vzdialené aspoň $d_{\min} \approx$ 1–1,5-násobok priemernej
   vzdialenosti bodov LHS ($\approx 10/\sqrt{N_0} \approx 0{,}9$).
3. **Krátke spresnenie:** Nelder–Mead z každého štartu s počiatočným
   simplexom veľkosti $\approx 0{,}5\, d_{\min}$, rozpočet napr. 25
   vyhodnotení na štart.
4. **Dokončenie:** najlepší výsledok spresňovať Nelder–Meadom so zvyšným
   rozpočtom (s reštartom simplexu, keď skolabuje); ak sa dosiahne veľmi
   malá veľkosť simplexu ($< 10^{-9}$), zvyšok rozpočtu použiť na ďalší štart
   z druhého najlepšieho povodia (poistka pre prípad, že sme „dno“ zamenili).

**Dôvod:** podľa zadania hlavné riziko je uviaznutie v lokálnom minime
**[Z]**, takže potrebujeme prieskum celej oblasti; Nelder–Mead je v 2D
efektívna lokálna metóda **[M]** a zároveň je priamo v prednáške EAL 5, takže
ho vieme dobre obhájiť. Štartovať z viacerých vzdialených bodov znižuje riziko,
že všetko minieme v jednom nesprávnom povodí.

**Čo chceme zistiť experimentom:** podiel prieskumu (20/40/60 %), počet
štartov $k$ (1/3/5), LHS vs. mriežka, Nelder–Mead (verzia z prednášky vs.
štandardná) vs. CRS. Hlavné ukazovatele: úspešnosť $\Delta < 10^{-8}$ a
počet vyhodnotení do jej dosiahnutia.

---

## 3. Stratégia pre `f20` (20D, 4000 vyhodnotení, natočené zle podmienené údolie)

> **Aktualizácia po etape 4 (K04):** experiment E21 ukázal, že CMA-ES pri rozpočte 4000
> nestihne konvergovať (medián medzery 20), kým BFGS s doprednými diferenciami dosiahne
> medzeru pod $10^{-8}$. Diagnostika D02 potvrdila hladkosť. Hlavnou metódou je preto
> **BFGS s multištartom**; CMA-ES ostáva ako alternatíva. Pôvodný návrh nižšie
> ponechávame kvôli dokumentácii rozhodovania.

### 3.1 Problém

Metóda sa musí prispôsobiť šikmému a pretiahnutému údoliu. Metódy po osiach
a izotropné metódy budú podľa teórie pomalé **[M]**. Nevieme, či je funkcia
hladká a či má jediné minimum.

### 3.2 Možnosti

| Varianta | Pre | Proti |
|---|---|---|
| A: vlastná CMA-ES s reštartmi | invariantná voči rotácii a lineárnej transformácii; odolná voči šumu a miernej multimodalite; dávkovanie | zložitejšia implementácia; učenie $\mathbf{C}$ spotrebuje časť rozpočtu |
| B: BFGS s gradientom z konečných diferencií | pri hladkej funkcii veľmi rýchla a presná konvergencia [M] | zlyhá pri šume/nehladkosti; presnosť obmedzená chybou diferencií |
| C: hybrid A → B | CMA-ES nájde údolie, BFGS dorazí posledné rády | dve metódy = viac miest na chybu; zmysel len ak B samotná zlyhá ďaleko od optima |
| D: $(1+1)$-ES | jednoduchá | izotropná, rýchlosť klesá s $\kappa$ [M] – iba referencia |

### 3.3 Odporúčanie: A ako hlavná vetva, B ako konkurent v E21, C až po výsledkoch

**Návrh A:**

- Štart: $\mathbf{m}_0$ = najlepší z malej LHS vzorky ($\approx 2n = 40$ bodov),
  $\sigma_0 \approx 2$ (asi 1/5 šírky oblasti), $\mathbf{C}_0 = \mathbf{I}$.
- Predvolené parametre podľa Hansenovho tutoriálu, $\lambda = 12$.
- Kandidáti generácie v jednej dávke, orezané do hraníc; do aktualizácie
  idú orezané body (teória, časť 11).
- Spektrálny rozklad $\mathbf{C}$ každú generáciu (pri $n = 20$ lacné).
- Ukončenie/reštart: ak $\sigma \cdot \max(\mathbf{D}) < 10^{-12}$, alebo sa
  najlepšia hodnota nezlepší za $10 + \lceil 30n/\lambda \rceil$ generácií,
  alebo je $\mathbf{C}$ numericky zle podmienená ($\kappa(\mathbf{C}) > 10^{14}$);
  reštart s dvojnásobným $\lambda$ (IPOP) zo zvyšného rozpočtu.

**Dôvod:** zadanie výslovne opisuje natočené zle podmienené údolie **[Z]**,
na ktoré je CMA-ES priamo navrhnutá **[M]**. Je robustnejšia ako BFGS, ak by
sa ukázalo, že funkcia nie je hladká. BFGS ponechávame ako vážneho
konkurenta – ak je funkcia hladká, môže byť rýchlejšia a presnejšia.

**Diagnostika pred tým (D02):** z dobrého bodu odhadnúť Hessovu maticu
konečnými diferenciami a pozrieť sa na vlastné čísla (podmienenosť) a vlastné
vektory (natočenie), plus overiť hladkosť (porovnať diferencie pre rôzne $h$).
Výsledok rozhodne, či má BFGS zmysel.

---

## 4. Stratégia pre `f2000` (2000D, 20 000 vyhodnotení, „zistiť, na čom záleží“)

### 4.1 Problém

Desať vyhodnotení na dimenziu. Zadanie naznačuje, že nie všetko je rovnako
dôležité **[Z]**, ale nevieme ako. Navyše náš kód musí mať náročnosť $O(n)$
na kandidáta (T00, R04).

> **Aktualizácia po etape 4:** D03 potvrdila H3 (9–18 silných premenných, ostatné
> takmer separabilné a lokálne kvadratické). Implementovaná je varianta „skríning →
> Newtonov krok na slabých premenných → CMA-ES v podpriestore silných premenných“.
> **Aktualizácia po etape 6 (K06):** v podpriestore silných premenných sa namiesto CMA-ES
> používa BFGS s multištartom a skríning má krok $h = 2$ (E30: medián medzery 1,57 → 0,34).

### 4.2 Najprv diagnostika (D03), až potom rozhodnutie

Navrhujem stratégiu **nevyberať naslepo**, ale najprv urobiť diagnostický
experiment na vývojových seedoch (mimo súťažného rozpočtu):

1. Skríning citlivosti zo stredu a z 2–3 náhodných bodov ($\pm h$, $h \in \{0{,}1;\ 1\}$):
   rozdelenie $|E_i|$ – je ich málo veľkých a veľa takmer nulových?
2. Stabilita poradia dôležitých premenných medzi základnými bodmi a medzi
   seedmi inštancie.
3. Test aditivity $I_{ij}$ na náhodnej vzorke dvojíc (dôležitých aj
   nedôležitých).

### 4.3 Možnosti podľa výsledku D03

| Výsledok D03 | Navrhovaná stratégia |
|---|---|
| **H3:** málo dôležitých premenných ($k \ll n$) | (1) skríning $n$–$2n$ vyhodnotení (10–20 % rozpočtu); (2) výber $k$ najdôležitejších (podľa zlomu v zoradených $|E_i|$, s hornou hranicou napr. 100); (3) CMA-ES v $k$-rozmernom podpriestore, ostatné premenné zafixované na najlepších hodnotách; (4) zvyšok rozpočtu na sep-ES vo všetkých premenných |
| **H3′:** všetky dôležité, separabilné | po súradniciach 1D minimalizácia (parabolická interpolácia z bodov skríningu $f_-, f_0, f_+$ → odhad minima v každej súradnici, potom ďalšie kolo) |
| ani jedno (husté interakcie) | sep-CMA-ES alebo $(1+1)$-ES v celom priestore s $\sigma$ adaptáciou; skríning len na nastavenie mierky jednotlivých súradníc |

**Pozn. k H3′:** ak je funkcia separabilná, z centrálneho skríningu
($f_-, f_0, f_+$ pre každú súradnicu, $2n + 1$ vyhodnotení) dostaneme pre
každú súradnicu parabolu a jej minimum

$$
x_i^{\text{nov}} = x_{0,i} - h\,\frac{f_+ - f_-}{2(f_+ - 2f_0 + f_-)} \quad (\text{ak } f_+ - 2f_0 + f_- > 0),
$$

a všetky súradnice môžeme posunúť naraz, lebo pri separabilite sa efekty
sčítajú. Je to Newtonov krok s diagonálnym Hessiánom. To je lacné a ak
hypotéza platí, veľmi účinné **[H]**.

### 4.4 Predbežné odporúčanie

Kým D03 nebeží: **východisková stratégia = skríning (centrálny, $2n+1$
vyhodnotení) → diagonálny Newtonov krok z neho (využije informáciu, aj keď
separabilita platí len približne) → sep-CMA-ES / $(1+1)$-ES so zvyškom
rozpočtu, s mierkou súradníc nastavenou podľa skríningu.** Táto kostra je
užitočná vo všetkých troch prípadoch a dá sa neskôr rozšíriť o podpriestorovú
CMA-ES, ak D03 potvrdí H3.

**Dôvod:** zadanie odporúča „najprv zistiť, na čom záleží“ **[Z]**; skríning
je presne to a stojí len 10–20 % rozpočtu. Zároveň nepredpokladáme výsledok
diagnostiky – kostra funguje aj vtedy, ak sa H3 nepotvrdí.

**Výpočtová kontrola:** všetko vektorizované; skríning = dve matice
$2000 \times 2000$ (32 MB každá) – lepšie po blokoch napr. po 500 riadkov,
aby sme nedržali v pamäti zbytočne veľké polia.

---

## 5. Odporúčaný postup ďalších etáp vzhľadom na termín

Priebežná kontrola: **ut 24. 11. 2026, 20:00** (2 body pre prvé tri tímy,
hodnotí sa hlavná vetva). Rozumiem, že zatiaľ nechceš nič nahrávať na git –
návrh preto počíta s tým, že kód pripravíme lokálne a o nahratí rozhodneš ty.

| Poradie | Krok | Výstup |
|---|---|---|
| 1 | Etapa 4: `spolocne.py` + referencie E01, E02 + jednoduchá verzia každej stratégie (f2 variant A, f20 CMA-ES, f2000 východisková kostra) | platný solver, testy zelené |
| 2 | Diagnostiky D01 (mapa f2), D02 (Hessián f20), D03 (skríning f2000) | podklady na rozhodnutia |
| 3 | Rozhodnutie o nahratí na main pred 24. 11. 20:00 (tvoje) | – |
| 4 | Etapy 5–6: porovnania E10, E11, E20, E21, E30, ladenie | `experimenty.md` |
| 5 | Etapy 7–8: finálny solver, README | odovzdanie |

## 6. Otvorené rozhodnutia pre teba

1. Súhlasíš so stratégiou A pre `f2` (prieskum + multištart Nelder–Mead)
   a CRS ako konkurentom?
2. Súhlasíš s CMA-ES ako hlavnou metódou pre `f20` a BFGS ako konkurentom?
3. Pri `f2000` najprv diagnostika D03 – súhlasíš, že môžem použiť veľké
   rozpočty na vývojových seedoch na zistenie štruktúry (je to v duchu zadania,
   ktoré to odporúča pre `f2`; na `f2000` nie je výslovne zakázané, ide len o
   lokálny vývoj)?
4. Kam dať experimentálne skripty – navrhujem `experimenty_blackbox/` v koreni
   repozitára.
