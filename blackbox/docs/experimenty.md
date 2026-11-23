# Experimentálny denník – black-box súťaž

Každý experiment má vlastný identifikátor. Zaznamenávajú sa aj neúspešné
experimenty. Výsledky sú iba skutočne namerané hodnoty; surové dáta sú v
`blackbox/vystupy/`. Plán experimentov je v `analyza_zadania.md`, časť 6.

**Spoločný protokol (ak nie je uvedené inak):** vývojové inštancie 1–5
(známe $f^*$), validačné inštancie 6–25 (referencia = najlepšia známa
hodnota, medzera je odhad), `rng_seed` 0–9, súťažné rozpočty. Hlavný
ukazovateľ je $\log_{10}\max(\Delta, 10^{-8})$ – medián a najhorší beh.

## Prehľad

| ID | Poradie | Funkcia | Algoritmus | Stav |
|---|---|---|---|---|
| T00 | 1 | všetky | technická kontrola rozhrania | vykonaný |
| D03 | 2 | `f2000` | diagnostika: skríning citlivosti, aditivita, podpriestor | vykonaný |
| D01 | 3 | `f2` | diagnostika: mapa krajiny | vykonaný |
| D02 | 4 | `f20` | diagnostika: Hessova matica, hladkosť | vykonaný |
| E21 | 5 | `f20` | CMA-ES (3 varianty) vs. BFGS (2 varianty) vs. $(1+1)$-ES | vykonaný – **CMA-ES neúspešná** |
| E21b | 6 | `f20` | BFGS na validačných inštanciách 6–25, voľba $h$ | vykonaný |
| E21c | 7 | `f20` | BFGS – počet bodov počiatočnej vzorky | vykonaný |
| E01 | 8 | všetky | náhodné hľadanie (referencia 1) | vykonaný |
| E02 | 8 | všetky | $(1+1)$-ES s pravidlom 1/5 (referencia 2) | vykonaný |
| E03 | 8 | všetky | `solve.py`, verzia etapy 4 | vykonaný |
| R01 | 9 | všetky | referenčné hodnoty pre validačné inštancie | vykonaný |
| E10/E11 | 10 | `f2` | podiel prieskumu, počet štartov, rozpočet na štart, varianta Nelder–Mead (72 kombinácií) | vykonaný |
| E22 | 11 | `f20` | BFGS: expanzia kroku, parabolická interpolácia, veľkosť vzorky | vykonaný |
| E23 | 12 | `f20` | krátke paralelné štarty proti lokálnym minimám | vykonaný – **bez zlepšenia** |
| E30 | 13 | `f2000` | $k$, $h$, $\sigma_0$, reštarty, 2. kolo Newtona, BFGS vs. CMA-ES v podpriestore | vykonaný |
| D04 | 14 | `f2000` | rozklad zvyškovej medzery (slabé vs. silné premenné) | vykonaný |
| E40 | 15 | všetky | `solve.py`, verzia po etape 6 | vykonaný |
| T01 | 16 | všetky | záverečná kontrola pravidiel v čistej kópii repozitára | vykonaný |

---

## T00 – Technická kontrola rozhrania a rýchlosti

- **Dátum / poradie:** 22. 11. 2026, 1.
- **Prostredie:** cloudové prostredie asistenta, Linux x86_64, Python 3.13,
  numpy 2.5.5, `omm_blackbox` 0.1.0 (wheel z vydania `blackbox-v0.1.0`).
  **Nie** Jozefov počítač.
- **Funkcie a seedy inštancií:** `f2`, `f20`, `f2000`, seed 1.
- **`rng_seed` algoritmu:** – (náhodné body z `default_rng(0)`, iba na meranie).
- **Testovaný algoritmus:** žiadny; volanie rozhrania.
- **Rozpočet:** veľký (10⁶) pre meranie času, 5 pre test vyčerpania.
- **Výsledky:**

| Kontrola | Výsledok |
|---|---|
| `f.dim`, `f.lower`, `f.upper` | 2 / 20 / 2000, všetky hranice −5 a 5 |
| pred prvým vyhodnotením | `best_x = None`, `best_y = inf` |
| bod `[6, 0]` | `ValueError`, nezapočítané |
| bod s `NaN` | `ValueError`, nezapočítané |
| zlý tvar (dĺžka 3 pri `f2`) | `ValueError`, nezapočítané |
| bod na hranici `[5, -5]` | vyhodnotený bez chyby |
| dávka 10 bodov pri zvyšku rozpočtu 5 | vyhodnotených 5, potom `BudgetExhausted`, `best_x` nastavené |
| `copy.deepcopy(f)` | `TypeError` |
| verejné atribúty | `batch, best_x, best_y, budget, dim, evaluations, lower, name, upper` |

| Funkcia | čas na bod, `f.batch` (1000 bodov) | čas na bod, `f(x)` (200 volaní) |
|---|---:|---:|
| `f2` | 0,3 µs | 1,3 µs |
| `f20` | 1,0 µs | 1,9 µs |
| `f2000` | 46,6 µs | 49,1 µs |

- **Čas vykonávania:** zanedbateľný.
- **Porovnanie s referenciou:** neaplikuje sa.
- **Interpretácia:** Rozhranie sa správa podľa zadania. Celý rozpočet `f2000`
  (20 000 bodov) sa dá vyhodnotiť približne za 1 s, teda časový limit 120 s
  ohrozuje iba výpočet samotného algoritmu. Dávkové vyhodnotenie je pri `f2`
  a `f20` rýchlejšie ako jednotlivé volania, pri `f2000` je rozdiel malý.
- **Rozhodnutie:** Pri `f2000` používať iba vektorizované operácie s
  náročnosťou $O(n)$ na kandidáta; všetky body pred vyhodnotením orezať do
  hraníc; veľkosť dávky orezať na zvyšok rozpočtu. Meranie zopakovať na
  Jozefovom počítači cez `spust_lokalne.py`.

---

## D03 – Diagnostika `f2000`: na ktorých premenných záleží

- **Dátum / poradie:** 22. 11. 2026, 2.
- **Skript:** `experimenty_blackbox/d03_skrining_f2000.py`, `d03b_podpriestor.py`, `d03c_slabe_premenne.py`.
- **Prostredie (platí aj pre ďalšie experimenty):** cloudové prostredie asistenta,
  Linux, Python 3.13, numpy 2.5.5, `omm_blackbox` 0.1.0. Nie Jozefov počítač.
- **Inštancie:** seedy 1–3 (skríning), 1–5 (podpriestor). Rozpočet neobmedzený – **iba diagnostika**, nie súťažný beh.
- **Postup:** centrálny skríning $f(\mathbf{x}_0 \pm h\mathbf{e}_i)$ zo stredu a z náhodného bodu,
  $h \in \{0{,}1;\ 1\}$; efekt $E_i = \max(|f_+ - f_0|, |f_- - f_0|)$; test aditivity $I_{ij}$
  na 30 dvojiciach; CMA-ES v podpriestore $k$ najdôležitejších premenných (30 000 vyhodnotení);
  diagonálny Newtonov krok.
- **Výsledky:**

| Zistenie | Hodnoty (seedy 1–3) |
|---|---|
| počet premenných s $E_i > 1\,\%$ max. efektu ($h = 1$) | 9–18 |
| najväčšie efekty ($h = 1$) | stovky až tisíce |
| medián efektu ($h = 1$) | $\approx 5 \cdot 10^{-4}$ |
| prekryv 50 najdôležitejších premenných (stred vs. náhodný bod) | 29–33 z 50 |
| aditivita medzi slabými premennými, max $|I_{ij}|$/efekt | $\le 1{,}1 \cdot 10^{-7}$ (prakticky separabilné) |
| aditivita medzi silnými premennými, max $|I_{ij}|$/efekt | 0,04–0,66 (interagujú) |
| slabé premenné: $c_i$ pri $h=1$ vs. $h=0{,}1$ (medián rel. rozdielu) | 0,75 % (lokálne takmer kvadratické) |
| slabé premenné: $c_i$ v strede vs. v náhodnom bode | 41 % (nie úplne kvadratické globálne) |
| diagonálny Newtonov krok iba na slabých premenných | zlepšenie 1,58 / 1,77 / 1,66 |
| diagonálny Newtonov krok na všetkých premenných | zhoršenie pri seedoch 2, 3 (silné premenné nie sú kvadratické) |

| Seed | medzera, CMA-ES v podpriestore $k=10$ | $k=20$ | $k=40$ |
|---|---:|---:|---:|
| 1 | 487 | 2,32 | 3,69 |
| 2 | 114 | 6,55 | 2,44 |
| 3 | 77,7 | 2,41 | 4,47 |
| 4 | 19,4 | 2,71 | 3,30 |
| 5 | 1684 | 8,77 | 3,09 |

- **Interpretácia:** Hypotéza H3 sa **potvrdila**: hodnotu funkcie určuje približne 10–20
  silných, navzájom interagujúcich premenných; zvyšných ≈ 1980 premenných má malý, takmer
  separabilný a lokálne kvadratický vplyv. Optimalizácia iba silných premenných nechá medzeru
  ≈ 2–4, čo zhruba zodpovedá zlepšeniu, ktoré dá Newtonov krok na slabých premenných (≈ 1,6–1,8).
  $k = 10$ je málo; medzi 20 a 40 nie je jednoznačný rozdiel.
- **Rozhodnutie:** stratégia pre `f2000`: skríning → Newtonov krok iba na slabých premenných →
  CMA-ES v podpriestore silných premenných, $k$ podľa prahu efektu s obmedzením $[10, 40]$.

## D01 – Mapa krajiny `f2`

- **Poradie:** 3. **Skript:** `experimenty_blackbox/d01_d02.py`. **Graf:** `blackbox/vystupy/d01_krajina_f2.png`.
- **Postup:** mriežka $201 \times 201$ na seedoch 1–5 (40 401 vyhodnotení – iba diagnostika).
- **Výsledky:** počet lokálnych miním na mriežke 29 / 39 / 56 / 45 / 30. Krajina má nepravidelné
  „hrbolaté“ pozadie a jedno výrazné hlboké, úzke, pretiahnuté a natočené údolie s globálnym
  minimom; pri seedoch 1 a 4 je aj druhé hlboké údolie, ktoré môže zmiasť (návnada).
- **Interpretácia:** potvrdzuje zadanie („vyzerá ako dno, a nie je“). Šírka globálneho údolia je
  rádovo 1, takže LHS so 120 bodmi (rozostup ≈ 0,9) ho väčšinou zasiahne.

## D02 – Hessova matica a hladkosť `f20`

- **Poradie:** 4. **Skript:** `experimenty_blackbox/d01_d02.py`.
- **Postup:** CMA-ES so 60 000 vyhodnoteniami (seedy 1–3), v nájdenom bode Hessova matica
  centrálnymi diferenciami ($h = 10^{-3}$).
- **Výsledky:**

| Seed | nájdená hodnota | známe $f^*$ | $\lambda_{\min}$ | $\lambda_{\max}$ | $\kappa$ |
|---|---:|---:|---:|---:|---:|
| 1 | 4,404178733 | 4,404178733 | 16,5 | 19 100 | 1 160 |
| 2 | 28,76735352 | 28,76735352 | 19,5 | 17 200 | 882 |
| 3 | 11,30171262 | 11,30171262 | 19,9 | 3 730 | 188 |

  Medián najväčšej zložky vlastných vektorov ≈ 0,5 (vektory nie sú rovnobežné s osami).
  Druhá derivácia v smere $x_1$ je rovnaká pre $h = 10^{-1}, 10^{-2}, 10^{-4}$ (rozdiel < 0,01 %).
- **Interpretácia:** potvrdené natočenie a zlé podmienenie v okolí optima; funkcia je **hladká**
  (žiadny šum), takže gradient z konečných diferencií je spoľahlivý → BFGS je vhodný kandidát.

## E21 – `f20`: CMA-ES vs. BFGS vs. $(1+1)$-ES

- **Poradie:** 5. **Skript:** `experimenty_blackbox/e21_f20_rychly.py`.
- **Inštancie:** 1–5; `rng_seed` 0–2; rozpočet 4000.

| Varianta | medián medzery | najhorší | medián $\log_{10}$ |
|---|---:|---:|---:|
| $(1+1)$-ES | 122 | 307 | 2,09 |
| CMA-ES, IPOP, reštart z najlepšieho | 20 | 107 | 1,30 |
| CMA-ES, IPOP, reštart z náhodného bodu | 20 | 107 | 1,30 |
| CMA-ES bez reštartu | 14,2 | 73,6 | 1,15 |
| BFGS, centrálne diferencie, $h = 10^{-5}$ | 0,077 | 32,6 | −1,11 |
| BFGS, dopredné diferencie, $h = 10^{-7}$ | $1{,}4 \cdot 10^{-9}$ | $2{,}6 \cdot 10^{-9}$ | −8,86 |

- **Interpretácia:** Pôvodne navrhnutá CMA-ES je pri rozpočte 4000 **neúspešná** – za 4000
  vyhodnotení sa nestihne naučiť kovariančnú maticu (v D02 potrebovala na presné optimum
  rádovo desiatky tisíc). Na hladkej funkcii BFGS využije informáciu z gradientu a dosiahne
  medzeru pod $10^{-8}$. Dopredné diferencie sú lepšie ako centrálne (polovičná cena gradientu).
- **Rozhodnutie:** `f20` → BFGS s doprednými diferenciami; CMA-ES ponechaná v kóde ako
  alternatíva (`strategia_f20_cma`), nepoužíva sa.

## E21b – `f20`: BFGS na validačných inštanciách, voľba $h$

- **Poradie:** 6. **Skript:** `experimenty_blackbox/e21b_bfgs_validacia.py`.
- **Inštancie:** 6–25 (referencia = najlepšia hodnota z dlhého BFGS a CMA-ES – medzera je odhad);
  `rng_seed` 0–2; rozpočet 4000; reštart BFGS z najlepšieho bodu.

| $h$ | medián medzery | najhorší | podiel $< 10^{-8}$ | medián vyhodnotení do $10^{-8}$ |
|---|---:|---:|---:|---:|
| $10^{-6}$ | $1{,}4 \cdot 10^{-8}$ | 21,9 | 43 % | 2324 |
| $10^{-7}$ | $1{,}6 \cdot 10^{-10}$ | 21,9 | 92 % | 2419 |
| $10^{-8}$ | $1{,}5 \cdot 10^{-12}$ | 21,9 | 92 % | 2419 |

- **Interpretácia:** $h = 10^{-6}$ je už príliš hrubé na presnosť $10^{-8}$. Zlyhania
  (seed 13, `rng_seed` 1; seed 14, `rng_seed` 0) **nie sú** spôsobené voľbou $h$: BFGS skončila
  v **lokálnom minime** s medzerou 16,8 a 21,9. `f20` teda nie je unimodálna.
- **Rozhodnutie:** $h = 10^{-7}$; po konvergencii BFGS ďalší štart z nového miesta (multištart),
  nie z najlepšieho bodu.

## E21c – `f20`: veľkosť počiatočnej vzorky pre BFGS

- **Poradie:** 7. **Skript:** `experimenty_blackbox/e21c_bfgs_start.py`.
- **Inštancie:** 1–25; `rng_seed` 0–3; multištart; štart z najlepšieho bodu LHS so $N$ bodmi.

| $N$ | podiel $< 10^{-8}$ | najhorší | medián vyhodnotení do $10^{-8}$ | 90 % kvantil |
|---|---:|---:|---:|---:|
| 0 (náhodný bod) | 93 % | 24,5 | 2480 | 3191 |
| 20 | 87 % | 25,1 | 2331 | 2792 |
| 50 | 95 % | 22,9 | 2404 | 3071 |
| 200 | 89 % | 27,4 | 2468 | 3052 |

- **Interpretácia:** rozdiely sú v rozsahu náhodného kolísania (100 behov na variantu); počiatočná
  vzorka podiel úspechov výrazne nemení. Jedna konvergencia BFGS trvá ≈ 2400 vyhodnotení, takže
  druhý štart sa do rozpočtu väčšinou nezmestí – to je hlavná slabina (≈ 5–10 % behov v lokálnom minime).
- **Rozhodnutie:** zatiaľ $N = 50$. Zrýchlenie konvergencie a lepšia voľba štartu sú úlohou etapy 6.

## E01, E02, E03 – referencie a `solve.py` (verzia etapy 4)

- **Poradie:** 8. **Skript:** `experimenty_blackbox/porovnanie.py`. **Dáta:** `blackbox/vystupy/porovnanie_E01_E03.csv`.
- **Inštancie:** 1–5 (známe $f^*$); `rng_seed` 0–9 (50 behov na funkciu a variantu); súťažné rozpočty.
- **Hyperparametre E03:** `f2` – LHS 40 % rozpočtu, 4 štarty po 25 vyhodnotení, štandardný
  Nelder–Mead; `f20` – BFGS, $h = 10^{-7}$, LHS 50 bodov, multištart; `f2000` – skríning $h = 1$,
  $k \in [10, 40]$ podľa prahu $10^{-3}$, CMA-ES v podpriestore, $\sigma_0 = 2$.

| Funkcia | Varianta | medián medzery | najhorší | medián $\log_{10}\max(\Delta,10^{-8})$ | podiel $< 10^{-8}$ | medián vyhodn. do $10^{-8}$ | max. čas |
|---|---|---:|---:|---:|---:|---:|---:|
| `f2` | E01 náhodné hľadanie | 1,31 | 5,21 | 0,12 | 0 % | – | 0,01 s |
| `f2` | E02 $(1+1)$-ES | 3,40 | 12,9 | 0,53 | 36 % | 204 | 0,01 s |
| `f2` | **E03 `solve.py`** | $6{,}9 \cdot 10^{-14}$ | 5,64 | −8,00 | **94 %** | 263 | 0,01 s |
| `f20` | E01 náhodné hľadanie | 16 800 | 33 800 | 4,23 | 0 % | – | 0,01 s |
| `f20` | E02 $(1+1)$-ES | 120 | 410 | 2,08 | 0 % | – | 0,13 s |
| `f20` | **E03 `solve.py`** | $1{,}5 \cdot 10^{-9}$ | $2{,}6 \cdot 10^{-9}$ | −8,00 | **100 %** | 2738 | 0,03 s |
| `f2000` | E01 náhodné hľadanie | 740 | 3 290 | 2,87 | 0 % | – | 2,44 s |
| `f2000` | E02 $(1+1)$-ES | 14,6 | 33,7 | 1,16 | 0 % | – | 2,61 s |
| `f2000` | **E03 `solve.py`** | 1,57 | 17,1 | 0,20 | 0 % | – | 1,23 s |

- **Porovnanie s referenciami:** `solve.py` porazil obe referencie pri všetkých troch funkciách
  v mediáne aj v najhoršom behu.
- **Interpretácia:**
  - `f2`: 47 z 50 behov našlo globálne minimum; 3 behy skončili v inom povodí (najhorší 5,64).
    Globálne minimum sa však dosahuje až okolo 263. vyhodnotenia – pri zhode s iným tímom
    rozhoduje rýchlosť, tu je priestor na zlepšenie.
  - `f20`: všetkých 50 behov pod $10^{-8}$ (na vývojových inštanciách; na validačných ≈ 92–95 %, E21b/E21c).
  - `f2000`: medián 1,57, ale najhorší 17,1 (seed 5) – CMA-ES v podpriestore niekedy uviazne.
  - Časy sú hlboko pod limitmi (30 / 60 / 120 s).
- **Rozhodnutie:** verzia je platná a porovnateľná; ďalšie zlepšenia patria do etáp 5–6
  (rýchlosť pri `f2`, lokálne minimá pri `f20`, robustnosť a slabé premenné pri `f2000`).

---

## R01 – Referenčné hodnoty pre validačné inštancie

- **Poradie:** 9. **Skript:** `experimenty_blackbox/referencie.py`; hodnoty v `experimenty_blackbox/referencie.json`.
- **Postup:** `f2` (seedy 6–25): mriežka $401 \times 401$ + Nelder–Mead z 10 najlepších bodov;
  `f20` (6–25): multištart BFGS so 400 000 vyhodnoteniami; `f2000` (6–15): `solve.py` s rozpočtom 300 000.
  Rámec `ramec.py` po každom behu referenciu prípadne zníži na najlepšiu nájdenú hodnotu.
- **Obmedzenie:** skutočné optimum nepoznáme, medzera je **odhad**. Pri `f2000` je referencia
  získaná našou vlastnou metódou, takže validačné výsledky pre `f2000` sú **skreslené
  v náš prospech** (medzera 0 znamená len „rovnako dobre ako náš najlepší beh“). Pre `f2000`
  preto rozhodujeme iba podľa inštancií 1–5 so známym optimom.

## E10/E11 – `f2`: delenie rozpočtu a lokálna metóda

- **Poradie:** 10. **Skript:** `experimenty_blackbox/e10_f2.py`.
- **Inštancie:** 1–25; `rng_seed` 0–9 (250 behov na kombináciu); rozpočet 300.
- **Hyperparametre:** podiel prieskumu $\in \{0{,}2;\ 0{,}3;\ 0{,}4;\ 0{,}5\}$, počet štartov $\in \{3, 5, 8\}$,
  rozpočet na štart $\in \{15, 25, 40\}$, Nelder–Mead štandardný / podľa prednášky.

| Varianta | podiel $< 10^{-8}$ | priemer $\log_{10}$ | najhorší | medián vyhodn. do $10^{-8}$ |
|---|---:|---:|---:|---:|
| E03 (0,4 / 4 štarty / 25 / štandard) | 97,0 % | −7,72 | 5,85 | 263 |
| **0,4 / 5 / 15 / štandard** (zvolené) | **98,8 %** | −7,90 | 5,85 | **247** |
| 0,4 / 5 / 25 / štandard | 98,8 % | −7,93 | 5,85 | 288 |
| 0,3 / 8 / 15 / štandard | 98,4 % | −7,86 | 5,81 | 263 |
| 0,3 / 5 / 15 / štandard | 97,2 % | −7,76 | 6,04 | 218 |
| 0,4 / 5 / 15 / prednáška | 97,6 % | −7,89 | 5,85 | 287 |
| 0,3–0,5 / 8 / 25 / prednáška | 0 % | ≈ −1,8 | ≈ 5 | – |

- **Interpretácia:** rozdiely medzi najlepšími nastaveniami sú malé (3 behy z 250). Viac štartov (5)
  pomáha nájsť správne povodie. Kratšie spresnenie (15) zrýchľuje dosiahnutie optima. Varianta
  Nelder–Mead z prednášky je pri malom rozpočte slabšia, lebo v každom kroku vyhodnocuje obe
  kontrakcie. Pri 8 štartoch po 25 vyhodnotení na dokončenie nezostane rozpočet, preto
  dosiahne 0 % (**neúspešná kombinácia**).
  Po stratégii nezostáva nevyužitý rozpočet; zlyhania (seed 4/`rng` 1, 14/5, 24/7) sú behy,
  v ktorých prieskum nezasiahol globálne údolie.
- **Rozhodnutie:** podiel 0,4, 5 štartov po 15 vyhodnotení, štandardný Nelder–Mead.

## E22 – `f20`: zlepšenie hľadania na priamke v BFGS

- **Poradie:** 11. **Skript:** `experimenty_blackbox/e22_f20.py`.
- **Inštancie:** 1–25; `rng_seed` 0–7 (200 behov); rozpočet 4000; $h = 10^{-7}$.
- **Diagnostika pred experimentom:** z náhodného štartu trvalo dosiahnutie medzery $10^2$
  približne 600–1300 vyhodnotení a medzery $1$ ďalších ≈ 1000 – BFGS robila priveľa krátkych krokov
  (spätné krokovanie iba skracuje krok, nikdy ho nepredĺži).

| Varianta | podiel $< 10^{-8}$ | priemer $\log_{10}$ | najhorší | medián vyhodn. do $10^{-8}$ |
|---|---:|---:|---:|---:|
| E03 (len spätné krokovanie) | 92 % | −7,34 | 22,9 | 2381 |
| + expanzia kroku (max. 6 zdvojnásobení) | 95 % | −7,57 | 22,9 | 1728 |
| + expanzia (max. 12) | 95 % | −7,57 | 22,9 | 1728 |
| + parabolická interpolácia | 96 % | −7,63 | 21,9 | 1494 |
| **+ expanzia + parabola** (zvolené) | **96 %** | −7,63 | 21,9 | **1484** |
| + expanzia, LHS 20 bodov | 95 % | −7,63 | 18,8 | 1693 |
| + expanzia, LHS 100 bodov | 93 % | −7,43 | 27,4 | 1788 |

- **Parabolická interpolácia:** z $f(\mathbf{x})$, sklonu $\nabla f^\top \mathbf{d}$ a $f(\mathbf{x} + \alpha\mathbf{d})$
  sa zostrojí parabola v premennej $\alpha$ a vyhodnotí sa jej minimum
  $\alpha^* = -\dfrac{\nabla f^\top \mathbf{d}\, \alpha^2}{2\,(f(\mathbf{x}+\alpha\mathbf{d}) - f(\mathbf{x}) - \nabla f^\top \mathbf{d}\, \alpha)}$
  (ak leží v $[0{,}1\alpha;\ 10\alpha]$).
- **Interpretácia:** lepšie hľadanie na priamke skrátilo konvergenciu o ≈ 38 % a zvýšilo podiel
  úspešných behov. Zvyšné ≈ 4 % zlyhaní sú lokálne minimá.
- **Rozhodnutie:** expanzia + parabola, LHS 50 bodov.

## E23 – `f20`: krátke paralelné štarty (neúspešný pokus)

- **Poradie:** 12. **Skript:** `experimenty_blackbox/e23_f20.py`. **Inštancie:** 1–25; `rng_seed` 0–7.
- **Hypotéza:** ak z $m$ štartov najprv spravíme krátke behy BFGS a pokračujeme iba z najlepšieho,
  vyhneme sa lokálnym minimám.

| Varianta | podiel $< 10^{-8}$ | najhorší | medián vyhodn. do $10^{-8}$ |
|---|---:|---:|---:|
| multištart (E22) | 96 % | 21,9 | 1484 |
| 2 štarty po 300 | 94 % | 21,9 | 1876 |
| 3 štarty po 200 | 95 % | 19,8 | 2004 |
| 3 štarty po 400 | 96 % | 13,4 | 2503 |
| 4 štarty po 250 | 92 % | 23,3 | 2367 |

- **Interpretácia:** hypotéza sa **nepotvrdila** – po 200–400 vyhodnoteniach ešte nevieme rozlíšiť,
  ktorý štart smeruje do globálneho minima, a strata rozpočtu spomalí konvergenciu.
- **Rozhodnutie:** ponechať jednoduchý multištart z E22.

## E30 – `f2000`: varianty skríningu a optimalizácie v podpriestore

- **Poradie:** 13. **Skript:** `experimenty_blackbox/e30_f2000.py`.
- **Inštancie:** 1–5 (známe $f^*$); `rng_seed` 0–9 (50 behov); rozpočet 20 000.
  (Prvé kolo bežalo aj na inštanciách 6–15, ale kvôli skresleniu referencií – R01 – sa podľa neho nerozhodovalo.)

| Varianta | medián medzery | najhorší | priemer $\log_{10}$ |
|---|---:|---:|---:|
| E03 ($h=1$, $k \in [10,40]$, CMA-ES) | 1,57 | 17,1 | 0,33 |
| $k = 20$ pevne | 0,91 | 17,1 | 0,22 |
| skríning $h = 2$ | 0,92 | 17,0 | 0,15 |
| $\sigma_0 = 3$ | 1,56 | 17,1 | 0,16 |
| $k = 20$, $h = 2$ | 0,84 | 17,0 | 0,18 |
| $k = 20$, $h = 2$, $\sigma_0 = 3$ | 1,32 | 17,0 | 0,17 |
| $k = 25$, $h = 2$ | 0,98 | 21,8 | 0,13 |
| $k = 15$, $h = 2$ | 1,76 | 243 | 0,52 |
| $k = 20$, $h = 2$, 2. kolo Newtona na slabých | 1,95 | 16,8 | 0,22 |
| $k = 20$, $h = 2$, CMA-ES s $4\lambda$ | 0,63 | 17,0 | −0,10 |
| $k = 20$, $h = 2$, reštart CMA-ES z náhodného bodu | 1,61 | 17,0 | 0,26 |
| $k = 20$, $h = 2$, **BFGS** v podpriestore | 0,32 | 5,88 | −0,09 |
| BFGS, $k = 20$, $h = 2$ + 2. kolo Newtona | 0,53 | 6,40 | −0,02 |
| BFGS, $k = 25$, $h = 2$ | 0,32 | 11,3 | 0,02 |
| BFGS, $k = 30$, $h = 2$ | 0,63 | 12,1 | 0,06 |
| BFGS, $k = 20$, $h = 1$ | 0,40 | 6,55 | −0,02 |
| **BFGS, $k \in [10, 40]$ podľa prahu, $h = 2$** (zvolené) | **0,34** | **5,88** | **−0,19** |

- **Interpretácia:** najväčší prínos má výmena CMA-ES za BFGS v podpriestore silných premenných –
  podobne ako pri `f20` je táto časť funkcie hladká a BFGS ju za rovnaký rozpočet dotiahne ďalej.
  Väčší krok skríningu ($h = 2$) spoľahlivejšie odlíši silné premenné. Druhé kolo Newtonovho kroku
  na slabých premenných stojí ≈ 4000 vyhodnotení a vychádza horšie, než keď tieto vyhodnotenia
  dostane BFGS (**neúspešná varianta**). Príliš malé $k = 15$ niekedy vynechá silnú premennú (najhorší 243).
- **Rozhodnutie:** $h = 2$, adaptívne $k \in [10, 40]$, BFGS s multištartom v podpriestore.

## D04 – `f2000`: z čoho sa skladá zvyšková medzera

- **Poradie:** 14. **Skript:** `experimenty_blackbox/d04_rezidua_f2000.py`. Iba diagnostika (veľký rozpočet).
- **Postup:** po behu verzie E03 (`rng_seed` 0): (1) päť kôl Newtonovho kroku iba na slabých premenných,
  (2) potom CMA-ES na 20 silných premenných so 100 000 vyhodnoteniami.

| Seed | medzera po E03 | po 5 kolách Newtona na slabých | potom po dlhej optimalizácii silných |
|---|---:|---:|---:|
| 1 | 0,87 | 0,65 | 0,16 |
| 2 | 4,45 | 4,22 | 0,16 |
| 3 | 2,70 | 2,46 | 0,81 |
| 4 | 1,57 | 1,36 | 0,18 |
| 5 | 16,46 | 16,24 | 10,59 |

- **Interpretácia:** slabé premenné tvoria iba ≈ 0,2 zvyškovej medzery; väčšina je v nedokonvergovanej
  alebo nesprávne zvolenej oblasti silných premenných. Pri seede 5 ani dlhá CMA-ES z daného bodu
  nepomohla – podpriestor silných premenných je **multimodálny**. To podporilo prechod na BFGS s multištartom (E30).

## E40 – `solve.py` po etape 6

- **Poradie:** 15. **Skript:** `experimenty_blackbox/e40_finalne.py`.

| Funkcia | Inštancie | `rng_seed` | medián medzery | najhorší | priemer $\log_{10}$ | podiel $< 10^{-8}$ | medián vyhodn. do $10^{-8}$ | max. čas |
|---|---|---|---:|---:|---:|---:|---:|---:|
| `f2` | 1–5 | 0–9 | 0 | 3,40 | −7,83 | 98 % | 247 | 0,02 s |
| `f2` | 6–25 | 0–9 | 0 | 5,85 | −7,91 | 99 % | 248 | 0,01 s |
| `f20` | 1–5 | 0–9 | $1{,}3 \cdot 10^{-9}$ | $2{,}5 \cdot 10^{-9}$ | −8,00 | 100 % | 1675 | 0,04 s |
| `f20` | 6–25 | 0–4 | $7 \cdot 10^{-11}$ | 21,9 | −7,63 | 96 % | 1452 | 0,03 s |
| `f2000` | 1–5 | 0–9 | 0,339 | 5,88 | −0,19 | 0 % | – | 0,81 s |
| `f2000` | 6–15 | 0–2 | (skreslené, R01) | 8,34 | – | – | – | 0,88 s |

(Medián medzery 0 pri `f2` znamená, že najlepší nájdený bod je rovnako dobrý ako referencia na
presnosť výpočtu.)

**Porovnanie s E03 (rovnaké inštancie 1–5, rovnaké `rng_seed`):**

| Funkcia | E03 medián / najhorší / úspešnosť | E40 medián / najhorší / úspešnosť | zmena |
|---|---|---|---|
| `f2` | $6{,}9 \cdot 10^{-14}$ / 5,64 / 94 % | 0 / 3,40 / 98 % | menej zlyhaní, rýchlejšie (263 → 247) |
| `f20` | $1{,}5 \cdot 10^{-9}$ / $2{,}6 \cdot 10^{-9}$ / 100 % | $1{,}3 \cdot 10^{-9}$ / $2{,}5 \cdot 10^{-9}$ / 100 % | rýchlejšie (2738 → 1675 vyhodn. do $10^{-8}$) |
| `f2000` | 1,57 / 17,1 / 0 % | 0,339 / 5,88 / 0 % | medián ≈ 4,6× menší, najhorší ≈ 2,9× menší |

- **Testy:** `pytest blackbox` – 30 testov prešlo. Max. čas behu 0,8 s (`f2000`), limity 30 / 60 / 120 s.


---

## T01 – Záverečná kontrola pravidiel

- **Dátum / poradie:** 23. 11. 2026, 16.
- **Prostredie:** cloudové prostredie asistenta, Linux; (a) Python 3.13 + numpy 2.5.5,
  (b) Python 3.11 + numpy 2.0.2 (najstaršie verzie povolené v `pyproject.toml`).
- **Postup:** čistá kópia tímového repozitára (šablóna) + naša zložka `blackbox/` a
  `experimenty_blackbox/`; spustené `pytest blackbox`, `blackbox/spust_lokalne.py --bez-zapisu`
  (3 seedy algoritmu) a `spust_vse.py`.

| Kontrola | Výsledok |
|---|---|
| `pytest blackbox` (a) | 30 prešlo |
| `pytest blackbox` (b) | 30 prešlo |
| `spust_lokalne.py`, `f2` | medián medzery 0, všetky behy „ok“ |
| `spust_lokalne.py`, `f20` | medián medzery $1{,}25 \cdot 10^{-9}$, všetky behy „ok“, max. 0,03 s |
| `spust_lokalne.py`, `f2000` | medián medzery 0,339, všetky behy „ok“, max. 0,86 s |
| `spust_vse.py` | časť black-box bez chyby (časti `model-uloha` a `simulacni-uloha` hlásia chybu šablóny, nesúvisí s riešičom) |
| importy v `blackbox/*.py` | `numpy`, `math`, `__future__`, `omm_blackbox`, vlastné moduly |
| čas, súbory, sieť, globálny stav | nepoužité |

- **Interpretácia:** riešič je platný v čistej kópii repozitára aj so staršími verziami knižníc.
- **Rozhodnutie:** odovzdať verziu E40 bez ďalších zmien kódu.
