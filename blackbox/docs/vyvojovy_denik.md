# Vývojový denník – black-box súťaž

Denník zaznamenáva každý významný krok vývoja solvera v poradí, v akom
prebehol. Pri krokoch, ktorých experiment ešte neprebehol, je výsledok
označený „Zatiaľ neoverené“. Značky zdrojov: **[Z]** zadanie, **[M]**
matematicky podložené, **[H]** hypotéza, **[O]** experimentálne overené.

---

## K01 – Analýza zadania (etapa 1)

**Dátum:** 22. 11. 2026

**Cieľ:** Pochopiť zadanie súťaže, zostaviť úplný kontrolný zoznam
povinných požiadaviek, identifikovať riziká neplatného behu a navrhnúť
postup ďalších etáp.

**Východiskový stav:** Máme oficiálne zadanie (snímky stránky súťaže v
češtine), šablónu repozitára (`blackbox/solve.py` s ukážkovým náhodným
hľadaním, `spust_lokalne.py`, testy v `blackbox/testy/`) a prednášky
Úvod do optimalizácie, Genetické algoritmy, Lineárne programovanie,
Nelineárna optimalizácia a KKT. Solver zatiaľ neexistuje.

**Matematické východiská:**
- Úloha: $\min_{\mathbf{x} \in [-5,5]^n} f(\mathbf{x})$ pre $n \in \{2, 20, 2000\}$,
  funkcia je čierna skrinka (bez predpisu a gradientu), rozpočet
  $B \in \{300, 4000, 20\,000\}$ vyhodnotení.
- Hodnotí sa medzera $\Delta = f(\mathbf{x}_{\text{best}}) - f^*$ na logaritmickej
  škále; $\Delta < 10^{-8}$ sa berie ako nula; pri zhode rozhoduje počet
  vyhodnotení.
- Pojmy použité v analýze: multimodalita a povodia príťažlivosti (`f2`),
  číslo podmienenosti $\kappa = \lambda_{\max}/\lambda_{\min}$ Hessovej matice a
  invariancia voči rotácii (`f20`), prekliatie dimenzionality a efektívna
  dimenzia (`f2000`).

**Hypotéza:**
- H1: Pri `f2` bude najlepšia kombinácia rovnomerného prieskumu a lokálneho
  spresnenia niekoľkých kandidátov.
- H2: Pri `f20` budú metódy invariantné voči rotácii (adaptácia plnej
  kovariancie, kvázi-Newton) výrazne lepšie ako metódy po osiach.
- H3: Pri `f2000` má funkcia nízku efektívnu dimenziu a oplatí sa začať
  skríningom citlivosti premenných (alternatíva H3′: separabilita).

**Rozhodnutie:**
- Etapu 1 zdokumentovať v `blackbox/docs/analyza_zadania.md`.
- Pre každú funkciu použiť samostatnú stratégiu (vetvenie podľa `f.name`).
- Vyhodnocovanie robiť cez jednu spoločnú obalovú funkciu, ktorá body vždy
  oreže do hraníc a dávku oreže na zvyšok rozpočtu.
- Experimentálne a grafové skripty neukladať do zložky `blackbox/` (test
  importov by ich kontroloval a zlyhal by na `matplotlib`/`pandas`).
- O priebehu algoritmu rozhodovať iba podľa počtu vyhodnotení, nikdy podľa
  nameraného času (inak by sa stratila reprodukovateľnosť).

**Zdôvodnenie:** Hodnotenie je pozičné a neplatný beh znamená posledné
miesto, preto má robustnosť (žiadne pády, žiadne prekročenie času)
prednosť pred ladením špičkového výkonu. Tri funkcie majú podľa zadania
úplne odlišný charakter, takže jediná univerzálna metóda by bola pre aspoň
jednu z nich zlá. Priebežná kontrola je už 24. 11. 2026 o 20:00, preto
treba čo najskôr mať platný referenčný solver na hlavnej vetve.

**Implementácia:** Zatiaľ žiadna zmena kódu. Vytvorené dokumenty:
`blackbox/docs/analyza_zadania.md`, `blackbox/docs/vyvojovy_denik.md`,
`blackbox/docs/experimenty.md`.

**Overenie:**
- Rozhranie modulu `omm_blackbox` 0.1.0 overené volaním v samostatnom
  cloudovom prostredí (Linux, Python 3.13, numpy 2.5.5) – experiment T00.
- V priečinku na Jozefovom počítači sa `uv sync` **nespúšťal** (prostredie
  asistenta je linuxové a vytvorilo by nekompatibilné `.venv`). Inštaláciu
  na Windows treba overiť lokálne.

**Výsledok:**
- [O] Rozhranie zodpovedá zadaniu; bod mimo hraníc, `NaN` aj zlý tvar
  vyvolajú `ValueError` bez započítania; čiastočná dávka sa vyhodnotí do
  vyčerpania rozpočtu a potom príde `BudgetExhausted`.
- [O] Vyhodnotenie je rýchle (pri `f2000` približne 47 µs na bod dávkovo,
  celý rozpočet okolo 1 s), takže časový limit ohrozuje iba náš vlastný
  výpočet.
- Výkon akejkoľvek optimalizačnej metódy: Zatiaľ neoverené.

**Interpretácia:** Pri `f2000` sú prípustné len metódy s výpočtovou
náročnosťou približne $O(n)$ na kandidáta; plná adaptácia kovariancie v
2000D je z časových dôvodov vylúčená. Pri `f2` a `f20` čas nie je
obmedzujúci.

**Obmedzenia:** Charakter funkcií poznáme iba zo slovného opisu v zadaní.
Hypotézy H1–H3 nie sú overené. Meranie rýchlosti prebehlo na inom stroji,
než je vyhodnocovací. Chýbajú informácie I1–I8 (`analyza_zadania.md`, časť 7),
najmä kde je tímový repozitár.

**Nasledujúci krok:** Po potvrdení etapa 2 (teória) a etapa 4 (referenčný
solver) v zhustenom režime: najprv jednoduchý platný solver pre všetky tri
funkcie, ktorý porazí náhodné hľadanie, a jeho nahratie na hlavnú vetvu
pred priebežnou kontrolou; potom diagnostiky D01–D03.

---

## K02 – Teoretická príprava (etapa 2)

**Dátum:** 22. 11. 2026

**Cieľ:** Vysvetliť optimalizačné metódy, ktoré prichádzajú do úvahy, ich
rovnice, náročnosť a vhodnosť pre `f2`, `f20` a `f2000`.

**Východiskový stav:** Etapa 1 hotová (K01). Doplnené prednášky EAL 04
(gradient, Hessián, numerické derivácie, najstrmší zostup, Newton), EAL 5
(Box–Wilson, Nelder–Mead, CRS, evolučné prehľadávanie) a EAL 6 (binárny GA).

**Matematické východiská:** náhodné hľadanie a pravdepodobnosť zásahu povodia;
LHS; kompasové hľadanie; Nelder–Mead v značení z prednášky
($\mathbf{M}, \mathbf{R}, \mathbf{E}, \mathbf{C}_1, \mathbf{C}_2, \mathbf{S}$);
CRS; binárny GA a rozlíšenie kódovania; $(1+1)$-ES s pravidlom 1/5; CMA-ES
a sep-CMA-ES; konečné diferencie, najstrmší zostup, Newton, BFGS; skríning
citlivosti, test aditivity, podpriestory; multištart; ošetrenie hraníc.

**Hypotéza:** Metódy invariantné voči rotácii budú na `f20` výrazne lepšie
ako metódy po osiach; binárny GA nebude konkurencieschopný pri žiadnej
funkcii; pre `f2000` sú prípustné len metódy s náročnosťou $O(n)$.

**Rozhodnutie:** Teóriu zapísať do `blackbox/docs/teoria.md` s jednotnou
štruktúrou pre každú metódu a súhrnnou tabuľkou vhodnosti. GA zdôvodnene
nezaradiť medzi hlavných kandidátov.

**Zdôvodnenie:** Jednotná štruktúra umožňuje porovnať metódy a obhájiť výber.
Vylúčenie GA je podložené vlastnosťami binárneho kódovania (nerešpektuje
spojitosť, kríženie viazané na osi, potreba veľa generácií) – nie je to
experimentálny záver.

**Implementácia:** Žiadna zmena kódu. Nový dokument `blackbox/docs/teoria.md`.

**Overenie:** Rovnice skontrolované voči prednáškam (Nelder–Mead podľa EAL 5,
numerické derivácie a Newton podľa EAL 04) a štandardným zdrojom uvedeným v
dokumente (CMA-ES podľa Hansenovho tutoriálu, BFGS podľa Nocedala a Wrighta).

**Výsledok:** Zatiaľ neoverené – žiadny optimalizačný experiment neprebehol.

**Interpretácia:** Teória dáva predbežné poradie kandidátov, ale nehovorí,
ako sa metódy správajú na konkrétnych skrytých funkciách.

**Obmedzenia:** Odhady počtu vyhodnotení (napr. koľko trvá naučenie
kovariancie pri `f20`) sú rádové a musia sa overiť.

**Nasledujúci krok:** Návrh stratégií (K03).

---

## K03 – Návrh stratégií (etapa 3)

**Dátum:** 22. 11. 2026

**Cieľ:** Navrhnúť konkrétny postup a delenie rozpočtu pre každú funkciu a
architektúru kódu.

**Východiskový stav:** K01, K02. Žiadne experimentálne dáta o funkciách.

**Matematické východiská:** pozri K02; navyše diagonálny Newtonov krok zo
skríningu pre separabilnú funkciu
$x_i^{\text{nov}} = x_{0,i} - h\,(f_+ - f_-)/(2(f_+ - 2f_0 + f_-))$.

**Hypotéza:**
- `f2`: LHS (≈ 40 % rozpočtu) + Nelder–Mead zo 4 vzdialených štartov +
  dokončenie najlepšieho dosiahne $\Delta < 10^{-8}$ vo väčšine behov.
- `f20`: vlastná CMA-ES s reštartmi porazí $(1+1)$-ES aj súradnicové hľadanie;
  BFGS môže byť lepšia, ak je funkcia hladká.
- `f2000`: skríning odhalí, na ktorých premenných záleží, a optimalizácia
  s touto informáciou porazí slepé metódy.

**Rozhodnutie:** Spoločná vrstva `spolocne.py` (vyhodnocovač s orezaním,
kontrolou rozpočtu a poistkou proti pádu) a samostatný modul pre každú
funkciu. `f2` – variant A (prieskum + multištart Nelder–Mead), CRS ako
konkurent. `f20` – CMA-ES s IPOP reštartmi, BFGS ako konkurent. `f2000` –
najprv diagnostika D03; dovtedy východisková kostra skríning → diagonálny
Newtonov krok → sep-ES. Experimentálne skripty mimo `blackbox/`.

**Zdôvodnenie:** Podrobne v `blackbox/docs/navrh_strategii.md` (pre každú
funkciu tabuľka možností s výhodami a nevýhodami).

**Implementácia:** Žiadna zmena kódu. Nový dokument
`blackbox/docs/navrh_strategii.md`.

**Overenie:** Zatiaľ len logická kontrola voči kontrolnému zoznamu P01–P18
(architektúra rieši P02–P07, P11, P13, P14).

**Výsledok:** Zatiaľ neoverené.

**Interpretácia:** –

**Obmedzenia:** Všetky číselné nastavenia (podiel prieskumu, počet štartov,
$\sigma_0$, $\lambda$, podiel skríningu) sú počiatočné odhady. Stratégia pre
`f2000` závisí od výsledku D03.

**Nasledujúci krok:** Po Jozefovom potvrdení etapa 4 – referenčná
implementácia (vyhodnocovač, E01, E02, prvé verzie stratégií) a diagnostiky
D01–D03. Nič sa nebude nahrávať na git bez Jozefovho súhlasu.

---

## K04 – Referenčná implementácia a diagnostiky (etapa 4)

**Dátum:** 22. 11. 2026

**Cieľ:** Vytvoriť platný, reprodukovateľný `solve.py` pre všetky tri funkcie, obe
referencie (náhodné hľadanie, $(1+1)$-ES) a podklady z diagnostík D01–D03.

**Východiskový stav:** Návrh z K03; žiadny kód okrem ukážky zo šablóny.

**Matematické východiská:** LHS, Nelder–Mead (teoria.md, časť 4), CMA-ES (7.2),
BFGS s doprednými diferenciami (8.1, 8.4), skríning a podpriestor (9.1, 9.4),
diagonálny Newtonov krok $x_i \leftarrow x_i - g_i / c_i$.

**Hypotéza:** H1 (`f2`: prieskum + Nelder–Mead), H2 (`f20`: metóda invariantná voči
rotácii, pôvodne CMA-ES), H3 (`f2000`: nízka efektívna dimenzia).

**Rozhodnutie:**
- `spolocne.py`: `Vyhodnocovac` (orezanie, kontrola rozpočtu, zachytenie
  `BudgetExhausted`), `Podpriestor`, LHS, výber vzdialených bodov.
- `metody.py`: náhodné hľadanie, $(1+1)$-ES, Nelder–Mead (štandardná a „prednášková“
  varianta), CMA-ES (plná aj diagonálna) s IPOP, BFGS s konečnými diferenciami.
- `strategie.py`: `f2` podľa návrhu; **`f20` zmenené z CMA-ES na BFGS** (E21);
  `f2000` skríning → Newtonov krok na slabých premenných → CMA-ES v podpriestore silných.
- `solve.py`: vetvenie podľa `f.name`, doplnenie nevyužitého rozpočtu, poistka proti
  pádu (`LADENIE = False`), ošetrenie záporného `rng_seed`.
- Experimentálne skripty v `experimenty_blackbox/` (mimo `blackbox/`, kvôli testu importov).

**Zdôvodnenie:** Zmena pre `f20` je experimentálne podložená: CMA-ES dosiahla medián
medzery 20, BFGS $1{,}4 \cdot 10^{-9}$ (E21). D02 ukázala, že funkcia je hladká, čo je
predpoklad BFGS. Pre `f2000` D03 potvrdila H3 (9–18 silných premenných, ostatné
takmer separabilné).

**Implementácia:** nové súbory `blackbox/spolocne.py`, `blackbox/metody.py`,
`blackbox/strategie.py`, `blackbox/testy/test_vlastne.py`; prepísaný `blackbox/solve.py`;
skripty `experimenty_blackbox/*.py`.

**Overenie:**
- `pytest blackbox`: 30 testov prešlo (9 zo šablóny + 21 vlastných: rozpočty 1 až
  20 000, využitie celého rozpočtu, vrátený bod je vyhodnotený a v hraniciach,
  zhoda celej postupnosti hodnôt pri rovnakom `rng_seed` pre všetky tri funkcie,
  veľké a záporné `rng_seed`).
- Testy bežia s `LADENIE = True`, aby poistka neskryla chyby.
- Spúšťané v cloudovom prostredí asistenta (Linux), **nie** na Jozefovom počítači.

**Výsledok (E01–E03, inštancie 1–5, 10 `rng_seed`):** medián medzery `solve.py`
$6{,}9 \cdot 10^{-14}$ (`f2`, 94 % behov pod $10^{-8}$), $1{,}5 \cdot 10^{-9}$ (`f20`,
100 %), 1,57 (`f2000`); obe referencie porazené vo všetkých troch funkciách.
Max. čas behu 1,2 s (`f2000`).

**Interpretácia:** Solver je platný a výrazne lepší ako referencie. Teoretický
predpoklad, že CMA-ES bude pre `f20` najlepšia, sa pri tomto rozpočte nepotvrdil.

**Obmedzenia:**
- `f2`: 6 % behov v nesprávnom povodí; globálne minimum sa dosahuje neskoro (≈ 263. vyhodnotenie).
- `f20`: ≈ 5–10 % behov na validačných inštanciách v lokálnom minime; jedna konvergencia
  BFGS trvá ≈ 2400 vyhodnotení, druhý štart sa nezmestí.
- `f2000`: najhorší beh 17,1 – CMA-ES v podpriestore niekedy uviazne; slabé premenné
  sa upravia iba jedným Newtonovým krokom.
- Výkon na tajných inštanciách je neznámy; validácia na seedoch 6–25 zatiaľ len pre `f20`.

**Nasledujúci krok:** Etapa 5–6: validácia `f2` a `f2000` na seedoch 6–25, porovnanie
variantov (E10, E11, E30) a cielené zlepšenia uvedených slabín. Rozhodnutie o nahratí
na git pred priebežnou kontrolou (24. 11. 2026, 20:00) je na Jozefovi.

---

## K05 – Experimentálne porovnanie (etapa 5)

**Dátum:** 23. 11. 2026

**Cieľ:** Spravodlivo porovnať varianty na väčšom počte inštancií a nájsť príčiny slabín
z K04.

**Východiskový stav:** `solve.py` z K04; slabiny: `f2` 6 % zlyhaní a neskoré dosiahnutie
optima, `f20` lokálne minimá a pomalá konvergencia BFGS, `f2000` medián 1,57 a najhorší 17,1.

**Matematické východiská:** párové porovnanie na rovnakých inštanciách a `rng_seed`;
ukazovateľ $\log_{10}\max(\Delta, 10^{-8})$, podiel behov pod $10^{-8}$, počet vyhodnotení
do $10^{-8}$.

**Hypotéza:** (a) pri `f2` pomôže viac štartov; (b) BFGS pri `f20` robí priveľa krátkych
krokov; (c) zvyšková medzera pri `f2000` je hlavne v silných premenných.

**Rozhodnutie:** spoločný rámec `experimenty_blackbox/ramec.py`; referenčné hodnoty pre
validačné inštancie 6–25 (R01); pri `f2000` rozhodovať len podľa inštancií 1–5.

**Zdôvodnenie:** Pri `f2000` sú referencie pre inštancie 6–15 získané našou metódou, preto by
porovnanie na nich bolo skreslené.

**Implementácia:** `experimenty_blackbox/ramec.py`, `referencie.py`, `e10_f2.py`, `e22_f20.py`,
`e23_f20.py`, `e30_f2000.py`, `d04_rezidua_f2000.py`.

**Overenie:** výsledky v `experimenty.md` (R01, E10/E11, E22, E23, E30, D04).

**Výsledok:** (a) potvrdené, 5 štartov po 15 vyhodnotení: 97 % → 98,8 %; (b) potvrdené,
diagnostika ukázala dlhé fázy malého postupu; (c) potvrdené (D04): slabé premenné ≈ 0,2
medzery, zvyšok sú silné premenné, ich podpriestor je multimodálny.

**Interpretácia:** Najväčšie rezervy boli v hľadaní na priamke (`f20`) a v metóde pre silné
premenné (`f2000`).

**Obmedzenia:** Referencie pre validačné inštancie sú odhady. Rozdiely okolo 1–2 % úspešnosti
sú na hranici náhodného kolísania.

**Nasledujúci krok:** K06 – zapracovať zlepšenia.

---

## K06 – Zlepšenie algoritmov (etapa 6)

**Dátum:** 23. 11. 2026

**Cieľ:** Zapracovať experimentálne podložené zmeny a overiť ich na rovnakých behoch ako K04.

**Východiskový stav:** K05.

**Matematické východiská:** expanzia kroku a parabolická interpolácia pri hľadaní na priamke
(teoria.md, časť 8.4); BFGS v podpriestore (časti 8.4 a 9.4).

**Hypotéza:** lepšie hľadanie na priamke zrýchli BFGS; BFGS bude v podpriestore silných
premenných `f2000` účinnejšia ako CMA-ES, lebo táto časť funkcie je hladká (rovnako ako `f20`).

**Rozhodnutie:**
- `f2`: podiel prieskumu 0,4, 5 štartov po 15 vyhodnotení (E10/E11).
- `f20`: BFGS s expanziou kroku a parabolickou interpoláciou (E22). Paralelné krátke štarty
  zamietnuté (E23 – bez zlepšenia).
- `f2000`: skríning s $h = 2$, BFGS s multištartom v podpriestore namiesto CMA-ES (E30).
  Druhé kolo Newtonovho kroku na slabých premenných zamietnuté (horšie).

**Zdôvodnenie:** každá zmena je podložená párovým porovnaním (tabuľky v `experimenty.md`).

**Implementácia:** `metody.bfgs_fd` – nové voľby `expanzia`, `parabola`, `tol_f`;
`strategie.strategia_f2000` – voľby `metoda`, `druhe_kolo`, `lam_nasobok`, nové predvolené
hodnoty; `strategie.strategia_f2`, `strategia_f20` – nové predvolené hodnoty.

**Overenie:** E40 na rovnakých inštanciách a `rng_seed` ako E03; `pytest blackbox` – 30 testov
prešlo; max. čas 0,8 s.

**Výsledok:**
- `f2`: úspešnosť 94 % → 98 % (inštancie 1–5), 99 % (6–25); dosiahnutie optima 263 → 247 vyhodnotení.
- `f20`: 100 % (1–5), 96 % (6–25); dosiahnutie $10^{-8}$ 2738 → 1675 vyhodnotení.
- `f2000`: medián medzery 1,57 → 0,339, najhorší 17,1 → 5,88.

**Interpretácia:** Pôvodný teoretický predpoklad, že CMA-ES bude vhodná pre zle podmienené
natočené funkcie, platí všeobecne, ale pri hladkých funkciách a malom rozpočte je metóda
využívajúca gradient z konečných diferencií výrazne efektívnejšia. Toto je hlavný experimentálny
poznatok projektu.

**Obmedzenia:**
- `f2`: ≈ 1–2 % behov nezasiahne globálne údolie.
- `f20`: ≈ 4 % behov skončí v lokálnom minime a druhý štart sa už nestihne dokonvergovať.
- `f2000`: medzera ≈ 0,3 je stále ďaleko od nuly; najhorší beh 5,9 (multimodalita silných
  premenných); ≈ 0,2 medzery pochádza zo slabých premenných.
- Všetko merané v cloudovom prostredí, nie na Jozefovom počítači ani vo vyhodnocovacom prostredí.

**Nasledujúci krok:** Etapa 7–8: finálna kontrola pravidiel, `blackbox/README.md` v slovenčine,
spustenie testov na Jozefovom počítači a rozhodnutie o nahratí na git pred
24. 11. 2026, 20:00.

---

## K07 – Záverečná kontrola pravidiel (etapa 7)

**Dátum:** 23. 11. 2026

**Cieľ:** Pred odovzdaním overiť, že riešič spĺňa všetky technické pravidlá súťaže
(kontrolný zoznam P01–P18 v `analyza_zadania.md`) a funguje so súbormi šablóny.

**Východiskový stav:** K06, verzia `solve.py` z experimentu E40.

**Matematické východiská:** neaplikuje sa (technická kontrola).

**Hypotéza:** Riešič je platný aj v čistej kópii tímového repozitára a aj s najstaršími
verziami, ktoré `pyproject.toml` povoľuje (Python 3.11, numpy 2.0).

**Rozhodnutie:** Kontrolu robiť v čistej kópii tímového repozitára (šablóna + naše súbory),
nie vo vývojovom priečinku.

**Zdôvodnenie:** Vyhodnocovateľ spúšťa repozitár, nie naše vývojové prostredie; skryté
závislosti od vývojových súborov by sa inak neprejavili.

**Implementácia:** žiadna zmena kódu.

**Overenie:** experiment T01 (`experimenty.md`):
- `pytest blackbox` – 30 testov prešlo (Python 3.13 + numpy 2.5 aj Python 3.11 + numpy 2.0.2);
- `spust_lokalne.py` zo šablóny a `spust_vse.py` – bez chýb v časti black-box, všetky behy „ok“;
- importy: iba `numpy`, `math`, `__future__`, `omm_blackbox` a vlastné moduly;
- v kóde nie je meranie času, práca so súbormi, sieť ani globálny stav medzi behmi;
- súbory šablóny okrem `solve.py` a `README.md` v `blackbox/` sú nezmenené (porovnanie MD5 s
  tímovým repozitárom).

**Výsledok:** Všetky kontroly prešli. Najdlhší beh 0,86 s pri limite 120 s.

**Interpretácia:** Riešič je pripravený na odovzdanie. Rezerva v čase je viac ako 100-násobná,
takže ani pomalší stroj vyhodnocovateľa nepredstavuje riziko.

**Obmedzenia:** Kontrola prebehla na Linuxe, nie na Windows ani vo vyhodnocovacom prostredí.
Spustenie `uv run pytest blackbox` na Jozefovom počítači je zatiaľ neoverené.

**Nasledujúci krok:** K08 – dokumentácia a odovzdanie.

---

## K08 – Dokumentácia a odovzdanie (etapa 8)

**Dátum:** 23. 11. 2026

**Cieľ:** Doplniť `blackbox/README.md` v slovenčine a pripraviť nahratie do tímového
repozitára pred priebežnou kontrolou 24. 11. 2026 o 20:00.

**Východiskový stav:** K07; `blackbox/README.md` bola česká šablóna s nevyplnenými časťami
„Strategie“ a „Experimenty“.

**Matematické východiská:** zhrnutie z `teoria.md` (BFGS, konečné diferencie, diagonálny Newtonov krok).

**Hypotéza:** neaplikuje sa.

**Rozhodnutie:** README zachová praktické informácie šablóny (spúšťanie, pravidlá importov) a
vyplní časti o stratégii a experimentoch. Podrobnosti ostávajú v `docs/`.

**Zdôvodnenie:** Šablóna žiada aspoň jedno porovnanie nastavení a popis, kde stratégia zlyháva;
README je prvé, čo hodnotiaci uvidí.

**Implementácia:** nový `blackbox/README.md`: tabuľka súborov, stratégia pre každú funkciu so
vzorcami, porovnanie s referenciami (E01–E03), zlepšenie E03 → E40, neúspešné pokusy a slabé miesta.

**Overenie:** čísla v README skontrolované proti tabuľkám E03 a E40 v `experimenty.md`.

**Výsledok:** Dokumentácia je kompletná.

**Interpretácia:** neaplikuje sa.

**Obmedzenia:** Nahratie do tímového repozitára robí Jozef cez webové rozhranie GitHubu;
stav nahratia zatiaľ neoverený.

**Nasledujúci krok:** Po nahratí skontrolovať obsah repozitára a spustiť testy z jeho čistej kópie.
