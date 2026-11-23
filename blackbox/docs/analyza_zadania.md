# Etapa 1 – Analýza zadania black-box súťaže

Tento dokument je výstupom etapy 1. Obsahuje výklad zadania, kontrolný zoznam
povinných požiadaviek so spôsobom overenia, technické a matematické riziká,
rozdiely medzi funkciami `f2`, `f20` a `f2000`, osnovu teoretickej dokumentácie,
plán experimentov a zoznam chýbajúcich informácií.

Každé tvrdenie je označené zdrojom:

| Značka | Význam |
|---|---|
| **[Z]** | povinná požiadavka alebo fakt z oficiálneho zadania (snímky stránky súťaže, šablóna repozitára) |
| **[M]** | matematicky podložená vlastnosť metódy alebo úlohy |
| **[H]** | naša pracovná hypotéza, zatiaľ neoverená |
| **[O]** | experimentálne overené zistenie (uvádza sa, kde a ako bolo overené) |

---

## 1. Výklad zadania

### 1.1 Matematická formulácia

Pre každú z troch funkcií hľadáme bod

$$
\mathbf{x}_{\text{best}} \approx \arg\min_{\mathbf{x} \in \Omega} f(\mathbf{x}),
\qquad \Omega = [-5, 5]^n, \quad n \in \{2, 20, 2000\}.
$$

**[Z]** O funkcii $f:\Omega \to \mathbb{R}$ vieme iba rozmer $n$ a hranice
$\Omega$. Nepoznáme jej predpis ani gradient; jediná operácia je dotaz
„aká je hodnota $f$ v bode $\mathbf{x}$?“, ktorý stojí jedno vyhodnotenie.
Počet vyhodnotení je pevne obmedzený rozpočtom $B$.

**[Z]** Globálne minimum $\mathbf{x}^*$ leží vo vnútri $\Omega$ (nie na hranici)
a jeho hodnota $f^* = f(\mathbf{x}^*)$ nie je nula. Z hodnoty funkcie preto
nevieme odhadnúť, ako ďaleko od optima sme.

Úloha je teda **optimalizácia s obmedzeniami typu box** (iba dolné a horné
hranice premenných), bez derivácií a s pevným rozpočtom. V terminológii
predmetu ide o bezderivačnú (*derivative-free*) optimalizáciu.

**[Z]** Každá funkcia je v skutočnosti *rodina* funkcií: konkrétna inštancia
vzniká zo seedu inštancie. Rovnaký seed dáva rovnakú funkciu, iný seed inú
funkciu „rovnakého charakteru“. Na vývoj máme verejné seedy 1–5 (a ich
optimá sú uvedené v `spust_lokalne.py`), hodnotí sa na tajných seedoch.

### 1.2 Hodnotiaca veličina

**[Z]** Po skončení behu sa vezme najlepší **skutočne vyhodnotený** bod a vypočíta
sa medzera k optimu

$$
\Delta = f(\mathbf{x}_{\text{best}}) - f(\mathbf{x}^*) \ge 0 .
$$

Medzera sa porovnáva na logaritmickej škále a zaokrúhlená; $\Delta < 10^{-8}$ sa
považuje za nulu. Pri zhode vyhráva tím, ktorý danú hodnotu dosiahol menším
počtom vyhodnotení.

Dôsledok **[M]**: keďže sa porovnáva $\log \Delta$, zlepšenie medzery z $10^{-2}$
na $10^{-4}$ má rovnakú váhu ako zlepšenie z $10^{2}$ na $10^{0}$. Oplatí sa
teda zlepšovať aj „malé“ medzery o rády, nielen sa dostať do blízkosti optima.

### 1.3 Bodovanie a termíny

**[Z]**
- V každom behu sa tímy zoradia; neplatný beh = posledné miesto v tomto behu.
- Poradie sa spriemeruje cez behy každej funkcie a potom cez tri funkcie
  s rovnakou váhou.
- **Priebežná kontrola: utorok 24. 11. 2026, 20:00.** Hodnotí sa obsah hlavnej
  vetvy repozitára v okamihu uzávierky. Prvé tri tímy dostanú 2 body.
- **Finále:** termín bude oznámený; nové tajné seedy; body 6 až 0 lineárne
  podľa poradia. Spolu za black box najviac 6 bodov.
- Referenčné stratégie v rebríčku: **náhodné hľadanie** a jednoduchá **(1+1)-ES**.

Dôsledok **[M]**: priemerovanie poradí znamená, že jeden neplatný beh (pád,
prekročený čas) stojí veľa – v danom behu sme poslední bez ohľadu na kvalitu
ostatných behov. **Robustnosť je dôležitejšia ako špičkový výsledok v jednom
behu.** Keďže každá funkcia má rovnakú váhu, slabá stratégia pre jednu funkciu
sa nedá vyvážiť výbornou stratégiou pre inú.

> **Termín:** dnes je nedeľa 22. 11. 2026. Do priebežnej kontroly zostávajú
> približne dva dni. Na získanie 2 bodov potrebujeme do **utorka 24. 11.,
> 20:00** mať na hlavnej vetve funkčný, platný a aspoň referenčné stratégie
> porážajúci `solve.py`. Navrhujem preto etapy 2–4 zhustiť (pozri časť 8).

### 1.4 Rozpočty a časové limity

| Funkcia | $n$ | Rozpočet $B$ | $B/n$ | Časový limit na beh **[Z]** |
|---|---:|---:|---:|---:|
| `f2` | 2 | 300 | 150 | 30 s |
| `f20` | 20 | 4 000 | 200 | 60 s |
| `f2000` | 2000 | 20 000 | 10 | 120 s |

**[Z]** Časový limit zahŕňa aj vyhodnocovanie funkcie a beží na jednom jadre.

**[O]** Orientačné meranie rýchlosti vyhodnotenia (cloudové prostredie, Linux,
`omm_blackbox` 0.1.0, numpy 2.5.5, pozri experiment T00 v `experimenty.md`):

| Funkcia | `f.batch` na 1 bod | `f(x)` na 1 bod | Celý rozpočet dávkovo |
|---|---:|---:|---:|
| `f2` | ≈ 0,3 µs | ≈ 1,3 µs | zanedbateľné |
| `f20` | ≈ 1,0 µs | ≈ 1,9 µs | zanedbateľné |
| `f2000` | ≈ 47 µs | ≈ 49 µs | ≈ 1 s |

Záver **[O]+[M]**: samotné vyhodnocovanie funkcie limity ani zďaleka nevyčerpá.
Riziko prekročenia času je v **našom vlastnom výpočte**, hlavne pri `f2000`:
napríklad úplná kovariančná matica $2000 \times 2000$ má $4 \cdot 10^6$ prvkov
a jej spektrálny rozklad stojí rádovo $n^3 = 8 \cdot 10^9$ operácií. Pri `f2000`
sú preto prípustné iba metódy s pamäťou a výpočtom približne $O(n)$ až
$O(n \cdot k)$ na jeden kandidátny bod, kde $k \ll n$.

### 1.5 Rozhranie modulu `omm_blackbox`

**[Z]** (a **[O]** – overené volaním v teste T00):

| Prvok | Význam |
|---|---|
| `Problem(name, seed, budget)` | inštancia funkcie (len na lokálny vývoj) |
| `f.name`, `f.dim` | `"f2"`/`"f20"`/`"f2000"`, rozmer |
| `f.lower`, `f.upper` | numpy polia dĺžky `dim` (−5 a 5) |
| `f.budget`, `f.evaluations` | rozpočet a doteraz spotrebované vyhodnotenia |
| `f(x)` | hodnota v bode, 1 vyhodnotenie |
| `f.batch(X)` | hodnoty v riadkoch matice `(k, dim)`, `k` vyhodnotení |
| `f.best_x`, `f.best_y` | najlepší doteraz vyhodnotený bod a hodnota (`None`, `inf` pred prvým vyhodnotením) |

Správanie overené v T00 **[O]**:
- Bod mimo hraníc, `NaN`/`inf` alebo zlý tvar vyvolá `ValueError` s českou
  správou a vyhodnotenie sa nezapočíta. Hranica ±5 je prípustná.
- Ak sa dávka nezmestí do zvyšku rozpočtu, vyhodnotia sa riadky, ktoré sa
  zmestia (započítajú sa aj do `best_x`), potom príde `BudgetExhausted`.
- Objekt nemá iné verejné atribúty, nedá sa skopírovať (`copy.deepcopy`
  zlyhá s `TypeError`).

### 1.6 Funkcia `solve`

**[Z]** Súbor `blackbox/solve.py` musí obsahovať

```python
def solve(f, rng_seed: int) -> np.ndarray:
    ...
    return np.asarray(f.best_x)
```

Volá sa pre každú funkciu, každú tajnú inštanciu a každý `rng_seed` zvlášť.
Funkciu rozoznáme podľa `f.name` alebo `f.dim` a smieme vetviť stratégiu.
Pomocné moduly zo zložky `blackbox/` sa smú importovať priamo
(`import pomocne`), `sys.path` sa nemá upravovať.

---

## 2. Kontrolný zoznam povinných požiadaviek

| ID | Požiadavka **[Z]** | Spôsob overenia |
|---|---|---|
| P01 | `blackbox/solve.py` obsahuje `solve(f, rng_seed: int) -> np.ndarray` s nezmenenou signatúrou | revízia kódu; `uv run pytest blackbox` (test importuje `solve`) |
| P02 | Všetka náhodnosť len z `np.random.default_rng(rng_seed)` alebo z neho odvodených generátorov; žiadne `np.random.seed()`, čas ani iný zdroj | revízia kódu (`grep` na `np.random.`, `random`, `time`); test `test_stejny_seed_stejny_vysledek`; vlastný test opakovaného behu pre všetky tri funkcie |
| P03 | Rovnaký `rng_seed` na rovnakej inštancii dá rovnaký výsledok | vlastný test: 2 behy, porovnanie `best_x`, `best_y` a celej postupnosti hodnôt (aj pre `f2000`) |
| P04 | Vrátený bod je skutočne vyhodnotený (najjednoduchšie `f.best_x`) | test `test_dodrzi_rozpocet_a_vrati_vyhodnoceny_bod`; `spust_lokalne.py` hlási „vrácený bod není f.best_x“ |
| P05 | Vrátený bod má tvar `(dim,)`, je konečný a v hraniciach | rovnaký test; `spust_lokalne.py` kontroluje tvar |
| P06 | Neprekročiť rozpočet; veľkosť dávky riadiť podľa `f.budget - f.evaluations` | test (porovnáva `f.evaluations <= rozpočet`); vlastný test s rôznymi rozpočtami (50, 200, 300, 500, 4000, 20 000) |
| P07 | Kandidátne body vždy v $[-5,5]^n$ (napr. `np.clip`) | `ValueError` by sa prejavil pádom; vlastný test so zachytením výnimiek |
| P08 | Časový limit 30 s / 60 s / 120 s na beh (1 jadro, vrátane vyhodnotení) | `spust_lokalne.py` meria čas a hlási prekročenie; cieľová rezerva aspoň 5× (pomalší stroj vyhodnocovateľa) |
| P09 | Žiadne hotové optimalizátory (`scipy.optimize`, `cma`, `optuna`, `nevergrad`, `pyswarms` …) | revízia kódu; `test_importy.py` |
| P10 | Importy len `numpy`, štandardná knižnica, `omm_blackbox` a vlastné moduly z `blackbox/` | `uv run pytest blackbox` (`test_importy.py` prechádza **všetky** `.py` v `blackbox/` okrem `spust_lokalne.py` a `testy/`) |
| P11 | Žiadna sieť, žiadne externé súbory, nič sa neukladá medzi behmi, nečítajú sa predpočítané výsledky | revízia kódu (`open`, `pathlib`, `urllib`, `socket`, globálne premenné prežívajúce medzi volaniami) |
| P12 | Férová hra: nesnažiť sa zistiť seed, optimum ani obísť počítadlo | revízia kódu; nepoužívať nič okrem verejného rozhrania |
| P13 | `solve` nesmie spadnúť; výnimka = neplatný beh (okrem `BudgetExhausted`) | testy na mnohých seedoch inštancií a `rng_seed`; ošetrenie hraničných prípadov (malý rozpočet, degenerovaný simplex, nulová smerodajná odchýlka …) |
| P14 | Solver funguje aj pri inom než súťažnom rozpočte (testy používajú 50/200/500 a 300) | vlastný test s malými rozpočtami; rozdelenie rozpočtu počítať z `f.budget`, nie z konštánt |
| P15 | Obsah hlavnej vetvy repozitára v čase uzávierky (24. 11. 2026, 20:00) | `git log origin/main`; čistý klon + `uv sync` + `uv run pytest blackbox` |
| P16 | `blackbox/README.md`: stručný opis stratégie pre každú funkciu a aspoň jedno porovnanie z vlastných experimentov vrátane toho, kde stratégia zlyháva | kontrola obsahu pred odovzdaním; každé číslo v README musí mať zdroj v `experimenty.md` / `vystupy/` |
| P17 | `uv.lock` commitnutý, `.venv/` nie | `git status`, `.gitignore` |
| P18 | Ak by sme potrebovali inú knižnicu než numpy, treba o ňu vopred požiadať | zatiaľ neplánujeme; ak áno, zapísať do `PRIDANE` v `test_importy.py` až po schválení |

Doplnkové požiadavky z tvojho zadania (nie z oficiálneho zadania, ale záväzné
pre našu spoluprácu): dokumentácia v spisovnej slovenčine (`README.md`,
`docs/vyvojovy_denik.md`, `docs/experimenty.md`), priebežne vedený denník,
zaznamenávanie aj neúspešných experimentov, LaTeX pre vzťahy, žiadne fiktívne
výsledky.

---

## 3. Riziká

### 3.1 Technické riziká neplatného behu

| ID | Riziko | Dôsledok | Opatrenie |
|---|---|---|---|
| R01 | Bod mimo hraníc po kroku mutácie, odrazení alebo numerickej chybe (napr. `5.0000000001`) | `ValueError` → pád → neplatný beh | Pred každým vyhodnotením `np.clip(X, lower, upper)` v jednej spoločnej obalovej funkcii |
| R02 | `NaN`/`inf` v kandidátovi (delenie nulou, pretečenie kroku $\sigma$, singulárna matica) | `ValueError` → pád | Kontrola `np.isfinite`; ohraničenie $\sigma$ zhora aj zdola; náhradný bod pri poruche |
| R03 | Dávka väčšia ako zvyšok rozpočtu | `BudgetExhausted` (beh platí, ale stratíme hodnoty dávky a riadenie toku) | Každú dávku orezať na `f.budget - f.evaluations`; centrálna obalová funkcia |
| R04 | Prekročenie času pri `f2000` (operácie $O(n^2)$, $O(n^3)$, Python cykly cez 2000 súradníc) | neplatný beh | Iba vektorizované operácie $O(n)$; meranie času; rezerva ≥ 5× |
| R05 | Zastavenie podľa nameraného času (`time.time()`) | rozbitá reprodukovateľnosť (výsledok závisí od rýchlosti stroja) | Rozhodovať iba podľa počtu vyhodnotení; čas nikdy nesmie ovplyvniť priebeh |
| R06 | Nepovolený import v pomocnom súbore alebo **v experimentálnom skripte uloženom v `blackbox/`** (napr. `matplotlib`, `pandas`, `scipy`) | spadnutý test, pri vyhodnotení `ImportError` | Experimentálne a grafové skripty dať **mimo zložky `blackbox/`** (alebo len s numpy); `uv run pytest blackbox` pred každým commitom |
| R07 | Malý rozpočet v testoch (50) pri stratégii, ktorá napevno počíta napr. so 100 bodmi počiatočného prieskumu | pád alebo nelogické správanie | Všetky podiely z `f.budget`; test s rozpočtami 1, 2, 10, 50 |
| R08 | Stav uložený mimo funkcie (globálne premenné, cache) prežíva medzi volaniami | porušenie P11 a reprodukovateľnosti | Všetok stav lokálne vo vnútri `solve` |
| R09 | Iná verzia numpy alebo Pythonu vo vyhodnocovacom prostredí (verzia nie je známa) | `AttributeError` pri novej funkcii numpy | Používať iba základné a dlho existujúce API numpy |
| R10 | `rng_seed` môže byť veľké alebo záporné celé číslo | `default_rng` záporné číslo odmietne | Overiť správanie; zadanie hovorí „celé číslo“ – v prípade potreby `abs()`/mapovanie, deterministicky |
| R11 | Návrat bodu, ktorý nie je `f.best_x` (napr. stred simplexu) | neplatný beh | Vždy `return np.asarray(f.best_x)` |
| R12 | Nedostatok času do priebežnej kontroly | strata 2 bodov | Najprv robustný referenčný solver na hlavnej vetve, potom zlepšovanie |
| R13 | Lokálny priečinok nemá `.git` – nevieme, kde je tímový repozitár | nič sa nevyhodnotí | Overiť (časť 7) |

### 3.2 Matematické a metodické riziká

| ID | Riziko | Opatrenie |
|---|---|---|
| M01 | Preučenie na piatich vývojových inštanciách; finále beží na nových seedoch **[Z]** | Ladiť na ďalších seedoch (napr. 6–25) s referenčnou hodnotou z dlhých behov; seedy 1–5 použiť ako kontrolu |
| M02 | `f2`: uviaznutie v lokálnom minime, ktoré „vyzerá ako dno“ **[Z]** | Rozdelenie rozpočtu na prieskum celej oblasti a viac lokálnych spresnení z rôznych povodí |
| M03 | `f20`: metódy pracujúce po osiach (súradnicové hľadanie, Hooke–Jeeves, diagonálne ES) sú na natočenom zle podmienenom údolí neefektívne **[Z]+[M]** | Uprednostniť metódy invariantné voči rotácii (adaptácia plnej kovariancie, kvázi-Newton s konečnými diferenciami) – overiť experimentom |
| M04 | `f2000`: 10 vyhodnotení na dimenziu je extrémne málo; naslepo „nenájdete nič“ **[Z]** | Najprv zistiť štruktúru (citlivosť premenných), až potom optimalizovať – hypotéza H3 nižšie |
| M05 | Hodnotenie je pozičné a zaokrúhlené; rozdiel v poslednom ráde nemusí znamenať lepšie poradie | Porovnávať $\log_{10}\Delta$, medián a najhorší beh, nie priemer $\Delta$ |
| M06 | Remíza pri `f2` (veľa tímov nájde globálne minimum) rozhoduje rýchlosť **[Z]** | Pri `f2` sledovať aj počet vyhodnotení do dosiahnutia $\Delta < 10^{-8}$ |
| M07 | Zámena hypotéz za fakty o tvare funkcií | Každý predpoklad o tvare funkcie označiť **[H]** a overiť diagnostickým experimentom |

---

## 4. Rozdiely medzi `f2`, `f20` a `f2000`

Všetky tri sú minimalizácia na $[-5,5]^n$ s optimom vo vnútri, ale každá
testuje inú vlastnosť solvera.

### 4.1 `f2` – multimodalita v malom rozmere

- **[Z]** $n = 2$, $B = 300$. „Veľa lokálnych miním. Ľahko uviaznete v niečom,
  čo vyzerá ako dno, a nie je.“
- **[Z]** Krajinu si môžeme vykresliť s veľkým rozpočtom na vývojových seedoch.
- **[M]** V 2D je $B/n = 150$ – rozpočet stačí na hustý prieskum. Pravidelná
  mriežka $17 \times 17 = 289$ bodov má krok $10/16 \approx 0{,}63$; ak sú
  povodia lokálnych miním menšie ako tento krok, samotná mriežka globálne
  minimum minie. Preto potrebujeme kombináciu prieskumu a lokálneho spresnenia.
- **[M]** Lokálne metódy (Nelder–Mead, $(1+1)$-ES, súradnicové hľadanie)
  konvergujú do minima povodia, v ktorom začnú. Globálny výsledok preto závisí
  od toho, či prieskum trafí správne povodie.
- **[H1]** Najlepšia bude stratégia „rovnomerný prieskum (mriežka alebo
  latinský hyperkocka / kvázináhodná postupnosť) → výber niekoľkých najlepších
  a navzájom vzdialených bodov → krátke lokálne spresnenie každého → dôkladné
  spresnenie najlepšieho“. Neoverené.
- **Kľúčová otázka:** aký podiel rozpočtu dať prieskumu a koľko kandidátov
  spresňovať. Pri remíze rozhoduje rýchlosť, takže príliš dlhý prieskum
  spomaľuje.

### 4.2 `f20` – zlé podmienenie a natočenie

- **[Z]** $n = 20$, $B = 4000$. „Zle podmienené, natočené údolie. Niektorými
  smermi funkcia prudko rastie, inými skoro vôbec, a tieto smery nie sú
  rovnobežné s osami.“
- **[M]** Pre lokálne kvadratický model
  $f(\mathbf{x}) \approx f^* + \tfrac12 (\mathbf{x}-\mathbf{x}^*)^\top \mathbf{H} (\mathbf{x}-\mathbf{x}^*)$
  je číslo podmienenosti $\kappa = \lambda_{\max}(\mathbf{H}) / \lambda_{\min}(\mathbf{H})$.
  Pri veľkom $\kappa$ sú vrstevnice pretiahnuté elipsoidy. Gradientný zostup
  s pevným krokom konverguje lineárne s pomerom približne
  $\left(\frac{\kappa-1}{\kappa+1}\right)$ na iteráciu, teda pomaly
  (prednáška Nelineárna optimalizácia – kroky gradientu kolmé na vrstevnice,
  „cik-cak“).
- **[M]** „Natočené“ znamená, že vlastné vektory $\mathbf{H}$ nie sú osi
  súradníc. Metódy, ktoré menia jednu súradnicu naraz alebo majú len
  diagonálnu adaptáciu mierky, sa nevedia prispôsobiť šikmému údoliu a robia
  veľa malých krokov. Potrebujeme metódu **invariantnú voči rotácii**, ktorá
  sa naučí smery údolia (napr. adaptácia plnej kovariančnej matice v ES, alebo
  kvázi-Newtonova aproximácia Hessovej matice).
- **[M]** V 20D je plná matica $20 \times 20$ výpočtovo lacná.
- **[H2]** Či je funkcia unimodálna a hladká, nevieme. Ak je hladká, môže byť
  silná aj kvázi-Newtonova metóda s gradientom z konečných diferencií (jeden
  gradient = 21 vyhodnotení dopredných alebo 40 centrálnych, teda približne
  100–190 gradientov). Ak je zašumená alebo nehladká, bude lepšia evolučná
  stratégia s adaptáciou kovariancie. Neoverené.

### 4.3 `f2000` – veľký rozmer a malý rozpočet na dimenziu

- **[Z]** $n = 2000$, $B = 20\,000$. „Je veľká. Naslepo v nej nenájdete nič;
  oplatí sa najprv zistiť, na čom záleží.“
- **[M]** $B/n = 10$. Už odhad gradientu konečnými diferenciami stojí $n+1 = 2001$
  vyhodnotení, teda takmer desatinu rozpočtu na **jediný** gradient.
- **[M]** Náhodné hľadanie v 2000D je beznádejné: aby sme sa náhodným bodom
  priblížili k optimu na vzdialenosť $\varepsilon$ v každej súradnici, potrebujeme
  rádovo $(10/\varepsilon)^n$ bodov (prekliatie dimenzionality).
- **[M]** Pri izotropnej $(1+1)$-ES na sférickej funkcii klesá optimálna
  rýchlosť konvergencie približne ako $1/n$ – teda v 2000D je postup na
  jedno vyhodnotenie zhruba stokrát pomalší ako v 20D.
- **[M]** Výpočtovo sú prípustné len metódy s nákladom $O(n)$ na kandidáta
  (pozri 1.4). Plná CMA-ES je vylúčená.
- **[H3]** Formulácia „zistiť, na čom záleží“ naznačuje, že funkcia má
  **nízku efektívnu dimenziu**: iba časť súradníc (alebo málo smerov) podstatne
  ovplyvňuje hodnotu, ostatné málo alebo vôbec. Potom by sa oplatilo minúť časť
  rozpočtu na **skríning citlivosti** (napr. zmena jednej súradnice naraz zo
  stredu, $\approx n$ až $2n$ vyhodnotení, alebo skupinový skríning), vybrať
  dôležité súradnice a optimalizovať v podpriestore. Je to iba hypotéza –
  musíme ju overiť diagnostickým experimentom, nie predpokladať.
- **[H3′]** Alternatíva: všetky súradnice sú dôležité, ale funkcia je
  separabilná alebo takmer separabilná. Vtedy by fungovala diagonálna
  adaptácia (sep-CMA-ES, súradnicové metódy). Aj toto treba overiť.

### 4.4 Súhrnné porovnanie

| Vlastnosť | `f2` | `f20` | `f2000` |
|---|---|---|---|
| Hlavná prekážka **[Z]** | veľa lokálnych miním | zlé podmienenie, natočenie | rozmer, málo vyhodnotení na dimenziu |
| $B/n$ | 150 | 200 | 10 |
| Dá sa vykresliť | áno | nie | nie |
| Výpočtová náročnosť nášho kódu | zanedbateľná | malá | rozhodujúca |
| Kandidáti na metódy | prieskum + multištart lokálnych metód (Nelder–Mead, pattern search, (1+1)-ES) | ES s adaptáciou plnej kovariancie; kvázi-Newton s konečnými diferenciami; (1+1)-ES ako referencia | skríning citlivosti + optimalizácia v podpriestore; ES s diagonálnou adaptáciou; súradnicové/blokové metódy |
| Pravdepodobne nevhodné **[M]/[H]** | čisté náhodné hľadanie, jediný lokálny štart | súradnicové hľadanie, Nelder–Mead v 20D, náhodné hľadanie | plná CMA-ES (čas), Nelder–Mead (2001 vrcholov), náhodné hľadanie |

---

## 5. Osnova matematicko-teoretickej dokumentácie

Návrh: teória bude v samostatnom súbore `blackbox/docs/teoria.md` (detailne,
na obhajobu) a v `README.md` iba jej skrátená verzia. Každá metóda bude mať
rovnakú štruktúru: princíp → rovnice a význam premenných → tvorba kandidátov →
aktualizácia → výpočtová náročnosť → počet vyhodnotení → silné/slabé stránky →
vhodnosť pre `f2`/`f20`/`f2000` → očakávanie pri obmedzenom rozpočte.

1. **Formulácia úlohy**
   1. Optimalizácia s obmedzeniami typu box, bezderivačná optimalizácia.
   2. Lokálne a globálne minimum, povodie príťažlivosti, multimodalita.
   3. Podmienenosť, Hessova matica, vlastné čísla, rotácia súradníc.
   4. Prekliatie dimenzionality, efektívna dimenzia.
   5. Prieskum verzus spresňovanie (*exploration – exploitation*), delenie rozpočtu.
   6. Ošetrenie hraníc (orezanie, odraz) a jeho vplyv na rozdelenie kandidátov.
2. **Referenčné metódy**
   1. Náhodné hľadanie – pravdepodobnosť zásahu okolia optima.
   2. $(1+1)$-ES s pravidlom 1/5 úspechu.
3. **Metódy prieskumu**
   1. Pravidelná mriežka, latinská hyperkocka, kvázináhodné postupnosti.
4. **Lokálne priame metódy**
   1. Súradnicové hľadanie a pattern search (Hooke–Jeeves).
   2. Nelderova–Meadova metóda (odraz, expanzia, kontrakcia, zmrštenie).
   3. Lokálne hľadanie s viacnásobnými reštartmi.
5. **Evolučné algoritmy**
   1. Evolučné stratégie $(\mu/\mu_w, \lambda)$, adaptácia veľkosti kroku (CSA).
   2. Adaptácia kovariančnej matice (CMA-ES), invariancia voči rotácii.
   3. Diagonálna varianta (sep-CMA-ES) pre veľký rozmer.
   4. Genetické algoritmy – princíp a prečo sú pri spojitej úlohe s malým
      rozpočtom menej vhodné (prednáška GA).
6. **Metódy s modelom gradientu**
   1. Konečné diferencie (dopredné, centrálne), chyba a cena.
   2. Gradientný zostup, kvázi-Newtonova metóda BFGS, line search.
7. **Metódy v podpriestoroch**
   1. Skríning citlivosti premenných (jedna premenná naraz, skupinový skríning).
   2. Optimalizácia v náhodných alebo vybraných podpriestoroch.
8. **Zvolené stratégie pre `f2`, `f20`, `f2000`** – prepojenie s experimentmi.
9. **Prepojenie rovníc s kódom** – tabuľka „rovnica → funkcia/riadok v `solve.py`“.

Teória je spracovaná v `teoria.md` (etapa 2), návrh stratégií v
`navrh_strategii.md` (etapa 3).

---

## 6. Plán experimentov

### 6.1 Všeobecný protokol

- **Inštancie:**
  - vývojové seedy 1–5, kde poznáme $f^*$ zo `spust_lokalne.py` → skutočná medzera $\Delta$;
  - validačné seedy, napr. 6–25, pre odhad zovšeobecnenia (ochrana proti
    preučeniu). Referenčnú hodnotu získame ako najlepšiu známu hodnotu z dlhých
    behov všetkých metód; medzera tu bude len **odhad** a bude tak označená.
- **Seedy algoritmu:** `rng_seed` = 0–9 (pri `f2` lacné, môžeme 0–29).
- **Rozpočty:** vždy súťažné (300 / 4000 / 20 000); ďalšie len pri
  diagnostike a vtedy zreteľne označené.
- **Ukazovatele (vopred určené):**
  1. $\log_{10} \max(\Delta, 10^{-8})$ – medián, najhorší beh, medzikvartilové rozpätie;
  2. podiel behov s $\Delta < 10^{-8}$ (úspešnosť, hlavne `f2`);
  3. počet vyhodnotení do dosiahnutia konečnej najlepšej hodnoty a do prahov
     $\Delta < 10^{-2}, 10^{-4}, 10^{-8}$;
  4. krivka konvergencie (najlepšia hodnota podľa počtu vyhodnotení);
  5. čas behu (maximum cez behy);
  6. počet pádov a neplatných behov (musí byť 0);
  7. simulované poradie: varianty zoradíme v každom behu a spriemerujeme poradie
     rovnako ako vyhodnocovateľ.
- **Spravodlivosť porovnania:** rovnaké inštancie, rovnaké `rng_seed`,
  rovnaký rozpočet, párové porovnanie (Wilcoxonov test so znamienkami v
  analytickom skripte mimo `blackbox/`).
- **Záznam:** každý experiment dostane ID a zápis v `experimenty.md`, surové
  výsledky v CSV v `blackbox/vystupy/`; aj neúspešné varianty.

### 6.2 Konkrétne experimenty

| ID | Funkcia | Cieľ | Porovnávané varianty |
|---|---|---|---|
| T00 | všetky | technická kontrola rozhrania a rýchlosti | – (čiastočne vykonané, pozri `experimenty.md`) |
| E01 | všetky | referencia 1: náhodné hľadanie zo šablóny | – |
| E02 | všetky | referencia 2: vlastná $(1+1)$-ES s pravidlom 1/5 | počiatočné $\sigma_0 \in \{0{,}5;\ 1;\ 2\}$ |
| D01 | `f2` | diagnostika: mapa krajiny (mriežka napr. $100 \times 100$ na seedoch 1–5, rozpočet 10 000 – len na pochopenie) | – ; zistiť počet a veľkosť povodí, či je štruktúra pravidelná |
| E10 | `f2` | prieskum + lokálne spresnenie | mriežka vs. latinská hyperkocka vs. náhodné body; podiel prieskumu 20 / 40 / 60 % |
| E11 | `f2` | voľba lokálnej metódy | Nelder–Mead vs. pattern search vs. lokálna $(1+1)$-ES; počet spresňovaných kandidátov 1 / 3 / 5 |
| D02 | `f20` | diagnostika: overiť zlé podmienenie a natočenie (odhad Hessovej matice konečnými diferenciami v okolí dobrého bodu, vlastné čísla a vlastné vektory) | – |
| E20 | `f20` | vplyv rotácie na metódy | súradnicové hľadanie vs. $(1+1)$-ES vs. Nelder–Mead (očakávame slabý výsledok – overenie [M03]) |
| E21 | `f20` | metódy invariantné voči rotácii | vlastná CMA-ES (rôzne $\lambda$, reštarty) vs. BFGS s konečnými diferenciami |
| D03 | `f2000` | diagnostika: skríning citlivosti (zmena jednej súradnice zo stredu o $\pm h$), rozdelenie efektov, separabilita (test aditivity na dvojiciach) | – ; overenie H3/H3′ |
| E30 | `f2000` | stratégie pre veľký rozmer | $(1+1)$-ES celý priestor vs. diagonálna ES / sep-CMA-ES vs. skríning + optimalizácia v podpriestore; podiel rozpočtu na skríning |
| E31 | `f2000` | čas | meranie času každej varianty, cieľ ≤ 24 s (rezerva 5×) |
| E40 | všetky | finálna kontrola | vybraná stratégia na validačných seedoch 6–25, 10 `rng_seed`, test reprodukovateľnosti |

Poradie realizácie je zvolené podľa termínu: najprv E01, E02 a jednoduchá
stratégia pre každú funkciu (priebežná kontrola), potom diagnostiky D01–D03 a
ich nadväzujúce porovnania.

---

## 7. Chýbajúce informácie

| # | Otázka | Prečo je dôležitá |
|---|---|---|
| I1 | **Kde je tímový repozitár na GitHube a ako odovzdávate?** Lokálny priečinok `sablona-repozitare` nemá `.git`. | Hodnotí sa hlavná vetva v čase uzávierky (P15, R13). |
| I2 | Je to tímový projekt (šablóna počíta s 3 členmi)? Kto robí black box? | Rozdelenie práce, README. |
| I3 | ~~Prednáška o Nelderovej–Meadovej metóde~~ – **vyriešené 22. 11. 2026** (dodané EAL 5 a EAL 04). | Teória a odkazy v dokumentácii. |
| I4 | Presné zaokrúhlenie medzery (na koľko rádov/desatinných miest v $\log_{10}$) a ako presne sa meria „rýchlosť“ pri remíze. Prípadne celé znenie stránky `blackbox.html`, ak obsahuje viac ako snímky. | Rozhoduje, či sa oplatí spresňovať posledné rády a ako rýchlo musíme nájsť optimum pri `f2`. |
| I5 | Počet tajných inštancií a `rng_seed` na funkciu (ak je známy). | Váha najhoršieho behu. |
| I6 | Verzia Pythonu a numpy vo vyhodnocovacom prostredí. | Riziko R09. |
| I7 | Dá sa na tvojom počítači spustiť `uv sync` a `uv run pytest blackbox`? | Ja som v tvojom priečinku `uv sync` **nespúšťal**: moje prostredie je Linux a vytvorilo by v tvojom priečinku linuxové `.venv`, ktoré by kolidovalo s Windows. Modul som overil v samostatnom cloudovom prostredí s linuxovým wheelom 0.1.0. Na Windows to treba spustiť u teba. |
| I8 | Smieme použiť vlastnú implementáciu známeho algoritmu (napr. CMA-ES)? Podľa textu zadania áno („celú stratégiu napíšete vlastným kódom“, zakázané sú hotové knižnice), ale ak si nie si istý, oplatí sa to potvrdiť u vyučujúceho. | Výber metód pre `f20`. |
