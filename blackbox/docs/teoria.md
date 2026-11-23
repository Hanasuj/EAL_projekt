# Etapa 2 – Teoretická príprava

Tento dokument vysvetľuje optimalizačné metódy, ktoré prichádzajú do úvahy pre
funkcie `f2`, `f20` a `f2000`. Pri každej metóde uvádzame princíp, rovnice,
tvorbu kandidátov, aktualizáciu, výpočtovú náročnosť, počet vyhodnotení,
silné a slabé stránky a vhodnosť pre jednotlivé funkcie.

Značky: **[Z]** zadanie, **[M]** matematicky podložené, **[H]** hypotéza
(zatiaľ neoverená), **[O]** experimentálne overené. V tejto etape **neprebehol
žiadny optimalizačný experiment**, preto všetky odhady správania na našich
funkciách sú **[H]**.

Zdroje z predmetu: *Úvod do optimalizace* (lokálne/globálne minimum, black-box,
prekliatie dimenzionality), *EAL 04* (gradient, Hessova matica, numerické
derivácie, najstrmší zostup, Newtonova metóda), *EAL 5* (Box–Wilsonova
metóda, Nelderov–Meadov algoritmus, CRS, evolučné prehľadávanie), *EAL 6*
(binárny GA), *Nelineární optimalizace a KKT* (podmienky optimality,
podmienenosť).

---

## 0. Spoločné označenie

| Symbol | Význam |
|---|---|
| $n$ | rozmer úlohy (2, 20, 2000) |
| $\Omega = [\mathbf{l}, \mathbf{u}] = [-5,5]^n$ | prípustná oblasť |
| $f(\mathbf{x})$ | účelová funkcia (čierna skrinka) |
| $\mathbf{x}^*$, $f^*$ | globálne minimum a jeho hodnota (neznáme) |
| $B$ | rozpočet vyhodnotení |
| $\mathbf{x}_k$ | aktuálny odhad riešenia v iterácii $k$ |
| $\sigma$ | veľkosť kroku (mierka mutácie) |
| $\mathbf{z} \sim \mathcal{N}(\mathbf{0}, \mathbf{I})$ | vektor nezávislých normovaných normálnych čísel |
| $\mathbf{e}_i$ | $i$-ty jednotkový vektor (smer osi $x_i$) |
| $\mathbf{H}$ | Hessova matica (matica druhých derivácií) |
| $\kappa = \lambda_{\max}(\mathbf{H}) / \lambda_{\min}(\mathbf{H})$ | číslo podmienenosti |

**Dve dôležité vlastnosti metód:**

- **Invariancia voči rotácii [M].** Metóda je invariantná voči rotácii, ak sa
  na funkcii $g(\mathbf{x}) = f(\mathbf{R}\mathbf{x})$ ($\mathbf{R}$ ortogonálna
  matica) správa rovnako ako na $f$. Pre `f20` je to kľúčové, pretože zadanie
  hovorí, že smery údolia nie sú rovnobežné s osami **[Z]**.
- **Výpočtová náročnosť na kandidáta.** Pri `f2000` rozhoduje, či metóda
  potrebuje $O(n)$, $O(n^2)$ alebo $O(n^3)$ operácií (pozri T00 a analýzu
  zadania, časť 1.4).

**Lokálny kvadratický model [M].** V okolí hladkého minima platí (Taylorov
rozvoj, EAL 04)

$$
f(\mathbf{x}) \approx f^* + \tfrac{1}{2}(\mathbf{x} - \mathbf{x}^*)^\top \mathbf{H} (\mathbf{x} - \mathbf{x}^*).
$$

Vrstevnice sú elipsoidy s osami v smeroch vlastných vektorov $\mathbf{H}$ a
dĺžkami poloosí úmernými $1/\sqrt{\lambda_i}$. Pomer najdlhšej a najkratšej
poloosi je $\sqrt{\kappa}$. Z toho plynie aj dôležitý vzťah pre presnosť:
medzera $\Delta$ rastie **kvadraticky** so vzdialenosťou od optima. Na
dosiahnutie $\Delta < 10^{-8}$ pri $\lambda \approx 1$ stačí vzdialenosť
približne $10^{-4}$.

---

## 1. Náhodné hľadanie (referencia 1)

**Princíp.** Body sa generujú nezávisle a rovnomerne v $\Omega$; pamätáme si
najlepší.

$$
\mathbf{x}^{(j)} \sim \mathcal{U}(\Omega), \quad j = 1, \dots, B, \qquad
\mathbf{x}_{\text{best}} = \arg\min_j f(\mathbf{x}^{(j)}).
$$

**Analýza [M].** Ak povodie globálneho minima (množina bodov, z ktorých by
lokálna metóda skončila v $\mathbf{x}^*$) zaberá podiel $p$ objemu $\Omega$,
pravdepodobnosť, že aspoň jeden z $B$ bodov doň padne, je

$$
P = 1 - (1 - p)^B .
$$

Pravdepodobnosť zásahu guľového okolia s polomerom $\varepsilon$ je úmerná
$(\varepsilon / 10)^n$, teda exponenciálne klesá s rozmerom (prekliatie
dimenzionality, *Úvod do optimalizace*).

**Náročnosť:** $O(n)$ na bod, $B$ vyhodnotení, triviálne dávkovanie.
**Silné stránky:** nemôže uviaznuť, nič nepredpokladá, ľahko sa dávkuje.
**Slabé stránky:** nevyužíva informáciu z predchádzajúcich bodov, nevie
spresňovať – medzera klesá veľmi pomaly.

**Vhodnosť:** `f2` – ako prieskumná fáza áno, ako celé riešenie nie (nedosiahne
presnosť $10^{-8}$). `f20`, `f2000` – nevhodné. Je to referencia, ktorú musíme
poraziť **[Z]**.

---

## 2. Rovnomerné pokrytie oblasti (mriežka, latinská hyperkocka)

**Princíp.** Namiesto nezávislých náhodných bodov chceme body rozložené
rovnomernejšie, aby v oblasti neostali veľké „diery“.

- **Pravidelná mriežka:** $m$ hodnôt na os, spolu $m^n$ bodov. Pre $n = 2$ a
  $m = 12$ je to 144 bodov s krokom $10/11 \approx 0{,}91$. Pre $n = 20$
  nepoužiteľné ($2^{20} \approx 10^6$ už pri $m = 2$).
- **Latinská hyperkocka (LHS):** každá os sa rozdelí na $N$ rovnakých
  intervalov a v každom intervale každej osi leží práve jeden bod:

$$
x^{(j)}_i = l_i + (u_i - l_i)\,\frac{\pi_i(j) + U^{(j)}_i}{N}, \qquad
U^{(j)}_i \sim \mathcal{U}(0,1),
$$

  kde $\pi_i$ je náhodná permutácia čísel $0, \dots, N-1$ pre os $i$.

**Náročnosť:** $O(Nn)$, $N$ vyhodnotení, dávkovanie triviálne.
**Silné stránky:** lepšie pokrytie ako náhodné hľadanie pri rovnakom počte
bodov; mriežka je deterministická. **Slabé stránky:** stále len prieskum,
nie spresnenie. Pravidelná mriežka môže systematicky minúť úzke povodia,
ak majú periodickú štruktúru zladenú s krokom mriežky **[M]**.

**Vhodnosť:** `f2` – prvá fáza (prieskum). Pre `f20`/`f2000` iba na
inicializáciu.

---

## 3. Súradnicové hľadanie, Box–Wilsonova metóda, pattern search

**Princíp (EAL 5).** Box–Wilsonova metóda porovná hodnoty v strede
$\mathbf{S}$ a v $2n$ bodoch okolo neho; presunie sa do najlepšieho bodu,
a ak je najlepší stred, skončí (alebo zmenší krok). Zovšeobecnenie je
**kompasové hľadanie (pattern search)**:

$$
\mathbf{y}_{i\pm} = \mathbf{x}_k \pm \delta_k \mathbf{e}_i, \quad i = 1, \dots, n,
$$

$$
\mathbf{x}_{k+1} =
\begin{cases}
\arg\min \{ f(\mathbf{y}_{i\pm}) \}, & \text{ak je lepší ako } f(\mathbf{x}_k),\\
\mathbf{x}_k, \;\; \delta_{k+1} = \delta_k / 2, & \text{inak.}
\end{cases}
$$

Varianta Hooke–Jeeves pridáva „zrýchľujúci“ krok v smere posledného úspešného
posunu.

**Náročnosť:** $2n$ vyhodnotení na jeden prieskum okolia, $O(n)$ výpočet.
**Silné stránky:** jednoduchá, robustná, dá sa vektorizovať (všetkých $2n$
bodov v jednej dávke). Pre hladké funkcie je známa teória konvergencie k
stacionárnemu bodu **[M]**.
**Slabé stránky:** **nie je invariantná voči rotácii** – kroky sú len po
osiach. V natočenom zle podmienenom údolí sa každý krok po osi takmer hneď
„odrazí“ od steny údolia, preto musí byť $\delta$ veľmi malé a postup pozdĺž
údolia je pomalý **[M]**. Pri $n = 2000$ stojí jeden prieskum 4000 vyhodnotení,
teda 5 takých krokov vyčerpá celý rozpočet.

**Vhodnosť:** `f2` – možné ako lokálne spresnenie. `f20` – podľa teórie zlé
(natočenie) **[M]**; v experimente E20 to chceme potvrdiť. `f2000` – len ak by
funkcia bola separabilná (hypotéza H3′).

---

## 4. Nelderova–Meadova metóda

**Princíp (EAL 5; Nelder a Mead, 1965).** Pracuje so simplexom z $n+1$ bodov
(v 2D trojuholník). V každej iterácii sa pokúsi nahradiť najhorší vrchol
lepším bodom pomocou odrazu, expanzie, kontrakcie alebo zmrštenia. Nepoužíva
derivácie, len porovnanie hodnôt.

**Rovnice (v značení z prednášky, zovšeobecnené na $n$ rozmerov).** Vrcholy
zoradíme podľa hodnoty: $\mathbf{B}$ (najlepší), $\mathbf{G}_1, \dots,
\mathbf{G}_{n-1}$ (dobré), $\mathbf{W}$ (najhorší).

$$
\mathbf{M} = \frac{1}{n}\Big(\mathbf{B} + \sum_{j=1}^{n-1}\mathbf{G}_j\Big) \quad \text{(ťažisko bez } \mathbf{W}\text{)}
$$

$$
\mathbf{R} = 2\mathbf{M} - \mathbf{W} \quad \text{(odraz)}, \qquad
\mathbf{E} = 2\mathbf{R} - \mathbf{M} \quad \text{(expanzia)},
$$

$$
\mathbf{C}_1 = \frac{\mathbf{W} + \mathbf{M}}{2}, \quad
\mathbf{C}_2 = \frac{\mathbf{M} + \mathbf{R}}{2} \quad \text{(vnútorná a vonkajšia kontrakcia)},
$$

$$
\mathbf{S}_j = \frac{\mathbf{B} + \mathbf{X}_j}{2} \quad \text{(zmrštenie všetkých vrcholov k } \mathbf{B}\text{)}.
$$

Slovne: $\mathbf{R}$ je zrkadlový obraz najhoršieho bodu cez ťažisko ostatných;
ak je odraz veľmi úspešný, skúsime ísť ešte ďalej ($\mathbf{E}$); ak nie je,
simplex sa zmenší smerom dovnútra ($\mathbf{C}$) alebo celý k najlepšiemu bodu
($\mathbf{S}$).

**Postup z prednášky:** (1) zoradiť vrcholy, (2) vypočítať $\mathbf{R}$,
(3a) ak je $\mathbf{R}$ lepší ako $\mathbf{W}$, vypočítať $\mathbf{E}$ a
$\mathbf{W}$ nahradiť lepším z $\mathbf{R}$, $\mathbf{E}$; (3b) inak vypočítať
$\mathbf{C}_1$, $\mathbf{C}_2$, lepší označiť $\mathbf{C}$; ak je $\mathbf{C}$
lepší ako $\mathbf{W}$, nahradiť (kontrakcia), inak zmrštiť.

Pozn.: štandardná verzia z literatúry je o niečo úspornejšia (expanziu skúša
len vtedy, keď je $\mathbf{R}$ lepší ako $\mathbf{B}$, a kontrakciu vyberá
podľa toho, či je $\mathbf{R}$ lepší ako $\mathbf{W}$ – vyhodnotí teda len
jeden z bodov $\mathbf{C}_1$, $\mathbf{C}_2$). Pri malom rozpočte môže
úspora vyhodnotení rozhodovať – je to kandidát na porovnanie **[H]**.

**Náročnosť:** $n+1$ vyhodnotení na počiatočný simplex, potom 1–2 vyhodnotenia
na bežnú iteráciu, $n$ pri zmrštení. Výpočet $O(n)$ na iteráciu (ťažisko sa dá
aktualizovať) plus triedenie. Metóda je **sekvenčná** – nedá sa dobre dávkovať.

**Silné stránky:** veľmi efektívna lokálna metóda v malom rozmere; prirodzene
sa prispôsobí tvaru údolia (simplex sa natiahne pozdĺž neho), čiastočne teda
zvláda aj natočenie; rýchla konvergencia v okolí hladkého minima v 2D.
**Slabé stránky:** iba lokálna – skončí v povodí, kde začala; s rastúcim
rozmerom sa simplex ľahko zdegeneruje (vrcholy ležia takmer v podpriestore)
a metóda sa zastaví. Sú známe príklady, kde konverguje k bodu, ktorý nie je
stacionárny (McKinnon, 1998) **[M]**. Preto sa v praxi používa s reštartmi.

**Vhodnosť:** `f2` – výborný kandidát na lokálne spresnenie z viacerých
štartov **[H]**. `f20` – použiteľná, ale v 20D býva pomalá a náchylná na
degeneráciu **[M]/[H]**. `f2000` – nepoužiteľná (2001 vrcholov = 10 %
rozpočtu len na počiatočný simplex, takmer žiadny postup).

---

## 5. Populačné metódy z predmetu: CRS a „evolučné prehľadávanie“

**Řízené náhodné prohledávání – CRS (EAL 5; Price, 1977).** Udržiavame
populáciu $N$ bodov. V každej iterácii náhodne vyberieme $n+1$ bodov (v 2D
tri), vytvoríme z nich simplex a urobíme odraz najhoršieho z nich cez ťažisko
ostatných. Ak je nový bod lepší ako **najhorší bod celej populácie**,
nahradí ho.

**„Evolučné prehľadávanie“ v podaní prednášky:** $M$ najlepších z $N$ prejde
do ďalšej iterácie, zvyšných $N-M$ sa vytvorí odrazmi náhodne vybraných
simplexov, nový bod sa prijme len ak nie je horší než najhorší z predchádzajúcej
iterácie, jeden náhodný jedinec sa nahradí náhodným bodom (mutácia).
Pozor: toto nie je evolučná stratégia v zmysle časti 7 – ide o variantu CRS.

**Náročnosť:** 1 vyhodnotenie na iteráciu (CRS) alebo $N - M$ na generáciu;
výpočet $O(n)$. **Silné stránky:** kombinuje globálny prieskum (populácia
pokrýva oblasť) a postupné sťahovanie k dobrým oblastiam; v 2D veľmi
prirodzené. **Slabé stránky:** pomalšia konvergencia v záverečnej fáze
(prednáška to uvádza pre CRS); v 20D a viac je reflexia náhodného simplexu
málo informatívna.

**Vhodnosť:** `f2` – zaujímavá alternatíva k „prieskum + Nelder–Mead“ **[H]**;
porovnanie navrhujeme v E11. `f20`, `f2000` – neodporúčame.

---

## 6. Genetické algoritmy

**Princíp (EAL 6).** Populácia jedincov zakódovaných binárne. Nová generácia
vzniká selekciou (napr. turnajom/soubojom), krížením (jednobodové kríženie
s pravdepodobnosťou $p_c$) a mutáciou (inverzia bitu s pravdepodobnosťou $p_m$);
elitárstvo zachová najlepšieho jedinca.

**Kódovanie.** Pri $b$ bitoch na premennú je rozlíšenie

$$
\Delta x = \frac{u - l}{2^b - 1} = \frac{10}{2^b - 1}.
$$

Na presnosť $10^{-4}$ (potrebnú na $\Delta < 10^{-8}$, pozri časť 0) treba
$b \ge 17$ bitov na premennú.

**Náročnosť:** $N$ vyhodnotení na generáciu; výpočet $O(Nnb)$.
**Silné stránky:** globálny charakter, odolnosť voči lokálnym minimám, dobre
sa dávkuje (celá generácia naraz).
**Slabé stránky pre našu úlohu [M]:**
- binárne kódovanie nerešpektuje spojitosť – susedné reálne hodnoty môžu mať
  veľmi odlišné kódy (napr. $0111\ldots1$ a $1000\ldots0$), mutácia bitu
  môže urobiť obrovský skok;
- jednobodové kríženie vymieňa celé súradnice, je viazané na osi, teda nie je
  invariantné voči rotácii (nevýhoda pre `f20`);
- GA typicky potrebujú desiatky generácií po desiatkach jedincov; pri
  $B = 300$ (`f2`) by to bolo napr. 15 generácií po 20, čo na spresnenie na
  $10^{-8}$ nestačí;
- v 2000D pri 20 000 vyhodnoteniach je to 10 vyhodnotení na premennú – GA
  nemá mechanizmus, ktorý by takto málo informácie využil efektívne.

**Vhodnosť:** pre všetky tri funkcie skôr nevhodné ako hlavná metóda. Ak by
sme GA chceli použiť, dávala by zmysel len reálne kódovaná varianta pri `f2`
ako prieskum. Navrhujeme GA nezaradiť do experimentov a v dokumentácii
zdôvodniť prečo (alebo urobiť jeden kontrolný beh v 2D, ak bude čas).

---

## 7. Evolučné stratégie

### 7.1 $(1+1)$-ES s pravidlom 1/5 (referencia 2)

**Princíp.** Jeden rodič $\mathbf{x}$ vytvorí jedného potomka mutáciou;
potomok nahradí rodiča, ak nie je horší. Veľkosť kroku sa prispôsobuje
podľa úspešnosti.

$$
\mathbf{y} = \mathbf{x} + \sigma \mathbf{z}, \qquad \mathbf{z} \sim \mathcal{N}(\mathbf{0}, \mathbf{I}),
$$

$$
\mathbf{x} \leftarrow
\begin{cases}
\mathbf{y}, & f(\mathbf{y}) \le f(\mathbf{x}),\\
\mathbf{x}, & \text{inak,}
\end{cases}
\qquad
\sigma \leftarrow \sigma \cdot \exp\!\left(\frac{\mathbb{1}[\text{úspech}] - 1/5}{d}\right),
$$

kde $d \approx \sqrt{n+1}$ je tlmiaca konštanta. **Pravidlo 1/5 (Rechenberg)
[M]:** ak je podiel úspešných mutácií väčší ako 1/5, krok je príliš malý a
zväčší sa; ak menší, krok sa zmenší. V ustálenom stave sa $\sigma$ zväčší
pri úspechu o faktor $e^{0{,}8/d}$ a zmenší pri neúspechu o $e^{-0{,}2/d}$,
čo je v rovnováhe práve pri úspešnosti 1/5.

**Teória [M].** Na sférickej funkcii s optimálne nastaveným $\sigma$ konverguje
lineárne (vzdialenosť klesá geometricky) s rýchlosťou približne $0{,}2/n$ na
jedno vyhodnotenie (normovaná rýchlosť postupu). Metóda je invariantná voči
rotácii (izotropná mutácia), ale **nie** voči zmene mierky v jednotlivých
smeroch: na elipsoide s číslom podmienenosti $\kappa$ sa rýchlosť zhorší
približne úmerne $1/\kappa$.

**Náročnosť:** $O(n)$ na kandidáta, 1 vyhodnotenie na iteráciu, sekvenčná.
**Silné stránky:** jednoduchá, robustná, malá réžia, dobrá referencia.
**Slabé stránky:** lokálna; pomalá pri zlom podmienení; pri $n = 2000$
pomalá kvôli faktoru $1/n$.

**Vhodnosť:** všetky tri funkcie ako referencia 2 **[Z]**. `f2000` – rozumná
východisková metóda, kým nevieme viac o štruktúre **[H]**.

### 7.2 $(\mu/\mu_w, \lambda)$-CMA-ES – adaptácia kovariančnej matice

**Princíp (Hansen a Ostermeier, 2001; Hansen, 2016).** Kandidáti sa vzorkujú
z viacrozmerného normálneho rozdelenia, ktorého stred, mierka aj tvar
(kovariančná matica) sa učia z úspešných krokov. Metóda sa tak „naučí“
natočenie a pretiahnutie údolia; v ideálnom prípade sa
$\mathbf{C} \propto \mathbf{H}^{-1}$ a zle podmienená úloha sa pre ňu
zmení na dobre podmienenú.

**Vzorkovanie** ($k = 1, \dots, \lambda$):

$$
\mathbf{x}_k = \mathbf{m} + \sigma\, \mathbf{B}\mathbf{D}\mathbf{z}_k, \qquad
\mathbf{z}_k \sim \mathcal{N}(\mathbf{0}, \mathbf{I}), \qquad
\mathbf{C} = \mathbf{B}\mathbf{D}^2\mathbf{B}^\top .
$$

$\mathbf{m}$ je stred rozdelenia (aktuálny odhad riešenia), $\sigma$ celková
veľkosť kroku, $\mathbf{C}$ kovariančná matica, $\mathbf{B}$ jej vlastné
vektory, $\mathbf{D}$ diagonála odmocnín vlastných čísel.

**Aktualizácia stredu.** Body zoradíme $f(\mathbf{x}_{1:\lambda}) \le \dots$
a zoberieme $\mu = \lfloor \lambda/2 \rfloor$ najlepších:

$$
\mathbf{m} \leftarrow \sum_{i=1}^{\mu} w_i\, \mathbf{x}_{i:\lambda}, \qquad
w_i \propto \ln\!\left(\mu + \tfrac12\right) - \ln i, \quad \sum w_i = 1, \qquad
\mu_{\text{eff}} = \frac{1}{\sum w_i^2}.
$$

**Evolučné cesty** (kumulované kroky stredu, $\mathbf{y}_w = (\mathbf{m}_{\text{nový}} - \mathbf{m}_{\text{starý}})/\sigma$):

$$
\mathbf{p}_\sigma \leftarrow (1 - c_\sigma)\mathbf{p}_\sigma + \sqrt{c_\sigma(2 - c_\sigma)\mu_{\text{eff}}}\; \mathbf{C}^{-1/2}\mathbf{y}_w,
$$

$$
\mathbf{p}_c \leftarrow (1 - c_c)\mathbf{p}_c + h_\sigma \sqrt{c_c(2 - c_c)\mu_{\text{eff}}}\; \mathbf{y}_w .
$$

**Aktualizácia kovariancie** (rank-one člen z evolučnej cesty + rank-$\mu$ člen z populácie):

$$
\mathbf{C} \leftarrow (1 - c_1 - c_\mu)\mathbf{C}
+ c_1 \mathbf{p}_c \mathbf{p}_c^\top
+ c_\mu \sum_{i=1}^{\mu} w_i\, \mathbf{y}_{i:\lambda}\mathbf{y}_{i:\lambda}^\top,
\qquad \mathbf{y}_{i:\lambda} = \frac{\mathbf{x}_{i:\lambda} - \mathbf{m}_{\text{starý}}}{\sigma}.
$$

**Aktualizácia veľkosti kroku (CSA):**

$$
\sigma \leftarrow \sigma \exp\!\left( \frac{c_\sigma}{d_\sigma}\left( \frac{\lVert \mathbf{p}_\sigma \rVert}{\mathbb{E}\lVert \mathcal{N}(\mathbf{0},\mathbf{I}) \rVert} - 1 \right) \right),
\qquad \mathbb{E}\lVert \mathcal{N}(\mathbf{0},\mathbf{I}) \rVert \approx \sqrt{n}\left(1 - \tfrac{1}{4n} + \tfrac{1}{21n^2}\right).
$$

Slovne: ak idú po sebe nasledujúce kroky stredu rovnakým smerom (cesta je
dlhšia ako pri náhodnej prechádzke), krok je zbytočne malý a $\sigma$ rastie;
ak sa navzájom rušia, $\sigma$ klesá.

**Predvolené parametre [M] (Hansen, 2016):** $\lambda = 4 + \lfloor 3\ln n \rfloor$
(pre $n = 20$: $\lambda = 12$, $\mu = 6$), $c_\sigma = \frac{\mu_{\text{eff}} + 2}{n + \mu_{\text{eff}} + 5}$,
$d_\sigma = 1 + 2\max\!\big(0, \sqrt{\frac{\mu_{\text{eff}} - 1}{n+1}} - 1\big) + c_\sigma$,
$c_c = \frac{4 + \mu_{\text{eff}}/n}{n + 4 + 2\mu_{\text{eff}}/n}$,
$c_1 = \frac{2}{(n+1{,}3)^2 + \mu_{\text{eff}}}$,
$c_\mu = \min\!\big(1 - c_1,\ \frac{2(\mu_{\text{eff}} - 2 + 1/\mu_{\text{eff}})}{(n+2)^2 + \mu_{\text{eff}}}\big)$.
Presné hodnoty pri implementácii prevezmeme z tutoriálu a uvedieme v kóde.

**Náročnosť:** vzorkovanie $O(n^2)$ na kandidáta, aktualizácia $\mathbf{C}$
$O(\mu n^2)$, spektrálny rozklad $O(n^3)$ (stačí raz za niekoľko generácií).
Pre $n = 20$ zanedbateľné. Pre $n = 2000$ neprijateľné (pozri analýzu, časť 1.4).
Generácia sa vyhodnotí jednou dávkou `f.batch`.

**Počet vyhodnotení.** Učiaca rýchlosť $c_\mu$ je rádovo $\mu_{\text{eff}}/n^2$;
naučenie plnej matice teda trvá rádovo desiatky až stovky generácií. Pre
$n = 20$ ($c_\mu \approx 0{,}01$) by to mohlo byť rádovo stovky až nízke tisíce
vyhodnotení – teda v rozpočte 4000 **pravdepodobne áno, ale tesne [H]**.
Musíme to overiť v E21.

**Silné stránky:** invariancia voči rotácii aj voči lineárnej transformácii
priestoru (po naučení $\mathbf{C}$) **[M]**; robustná voči šumu a miernej
multimodalite; dobre sa dávkuje.
**Slabé stránky:** zložitejšia implementácia (veľa parametrov, ľahko sa
spraví chyba); pri malom rozpočte strávi časť vyhodnotení učením $\mathbf{C}$;
výpočtovo $O(n^2)$–$O(n^3)$.

**Vhodnosť:** `f20` – hlavný kandidát **[H]**. `f2` – použiteľná, ale v 2D
s 300 vyhodnoteniami pravdepodobne neprekoná multištart Nelder–Mead.
`f2000` – len diagonálna varianta (7.3) alebo v malom podpriestore (časť 9).

### 7.3 sep-CMA-ES (diagonálna kovariancia)

**Princíp (Ros a Hansen, 2008).** $\mathbf{C}$ sa obmedzí na diagonálnu maticu,
teda učí sa iba mierka každej súradnice, nie natočenie:

$$
\mathbf{x}_k = \mathbf{m} + \sigma\, \mathbf{d} \odot \mathbf{z}_k, \qquad
d_i^2 \leftarrow (1 - c_1' - c_\mu') d_i^2 + c_1' p_{c,i}^2 + c_\mu' \sum_i w_i\, y_{i:\lambda, i}^2,
$$

s učiacimi rýchlosťami zväčšenými približne o faktor $(n+2)/3$, pretože
učíme len $n$ čísel namiesto $n(n+1)/2$.

**Náročnosť:** $O(n)$ na kandidáta – pri $n = 2000$ prijateľné.
**Silné stránky:** zvládne rôzne citlivé súradnice (napr. ak na niektorých
premenných „nezáleží“ – ich mierka sa nemení alebo rastie). **Slabé stránky:**
nevie natočenie; pri 10 vyhodnoteniach na dimenziu sa ani diagonála nemusí
stihnúť naučiť **[H]**.

**Vhodnosť:** `f2000` – kandidát, najmä ak platí H3′ (separabilita) alebo H3
(málo dôležitých premenných) **[H]**.

---

## 8. Metódy využívajúce gradient z konečných diferencií

### 8.1 Odhad gradientu (EAL 04)

$$
\text{dopredná: } \frac{\partial f}{\partial x_i} \approx \frac{f(\mathbf{x} + h\mathbf{e}_i) - f(\mathbf{x})}{h}, \quad \text{chyba } O(h), \quad n \text{ vyhodnotení};
$$

$$
\text{centrálna: } \frac{\partial f}{\partial x_i} \approx \frac{f(\mathbf{x} + h\mathbf{e}_i) - f(\mathbf{x} - h\mathbf{e}_i)}{2h}, \quad \text{chyba } O(h^2), \quad 2n \text{ vyhodnotení}.
$$

**Voľba $h$ [M].** Príliš veľké $h$ → chyba aproximácie; príliš malé $h$ →
chyba zaokrúhlenia. Pri dvojnásobnej presnosti ($\varepsilon \approx 2{,}2\cdot 10^{-16}$)
je rozumné $h \approx \sqrt{\varepsilon} \approx 10^{-8}$ pre doprednú a
$h \approx \varepsilon^{1/3} \approx 10^{-5}$ pre centrálnu diferenciu
(škálované veľkosťou $x$). Prednáška ukazuje, že pre Rosenbrockovu funkciu
funguje aj pomerne veľké $h$. Ak je funkcia nehladká alebo zašumená, odhad
gradientu je nespoľahlivý **[M]** – to zatiaľ nevieme **[H]**.

Body $\mathbf{x} \pm h\mathbf{e}_i$ sa dajú vyhodnotiť jednou dávkou.

### 8.2 Najstrmší zostup

$$
\mathbf{x}_{k+1} = \mathbf{x}_k - a_k \nabla f(\mathbf{x}_k).
$$

**Teória [M].** Na kvadratickej funkcii s presným hľadaním na priamke klesá
$f(\mathbf{x}_k) - f^*$ najmenej s faktorom $\left(\frac{\kappa - 1}{\kappa + 1}\right)^2$
na iteráciu. Pri $\kappa = 10^4$ je to $\approx 0{,}9996$ – prakticky stojí.
Prednáška ukazuje aj citlivosť na veľkosť kroku $a$ (pri Rosenbrockovej
funkcii $a = 0{,}0021$ už diverguje, $a = 0{,}0020$ konverguje). Pre `f20`
preto nevhodný.

### 8.3 Newtonova metóda (EAL 04)

$$
\mathbf{x}_{k+1} = \mathbf{x}_k - \mathbf{H}_k^{-1} \nabla f(\mathbf{x}_k).
$$

Vychádza z minimalizácie kvadratického modelu; na kvadratickej funkcii nájde
minimum v jednom kroku, pri Rosenbrockovej funkcii v prednáške v štyroch.
**Cena:** numerický Hessián potrebuje rádovo $2n^2$ vyhodnotení
($n = 20$: približne 800), čo si pri `f20` môžeme dovoliť iba raz – dvakrát.

### 8.4 Kvázi-Newtonova metóda BFGS

Namiesto výpočtu Hessovej matice ju aproximuje z rozdielov gradientov.
Pre inverznú aproximáciu $\mathbf{V}_k \approx \mathbf{H}^{-1}$:

$$
\mathbf{s}_k = \mathbf{x}_{k+1} - \mathbf{x}_k, \qquad
\mathbf{y}_k = \nabla f(\mathbf{x}_{k+1}) - \nabla f(\mathbf{x}_k), \qquad
\rho_k = \frac{1}{\mathbf{y}_k^\top \mathbf{s}_k},
$$

$$
\mathbf{V}_{k+1} = (\mathbf{I} - \rho_k \mathbf{s}_k \mathbf{y}_k^\top)\, \mathbf{V}_k\, (\mathbf{I} - \rho_k \mathbf{y}_k \mathbf{s}_k^\top) + \rho_k \mathbf{s}_k \mathbf{s}_k^\top,
\qquad \mathbf{d}_k = -\mathbf{V}_k \nabla f(\mathbf{x}_k).
$$

Krok $\mathbf{x}_{k+1} = \mathbf{x}_k + \alpha_k \mathbf{d}_k$, kde $\alpha_k$
sa hľadá na priamke (napr. spätným krokovaním s Armijovou podmienkou
$f(\mathbf{x}_k + \alpha\mathbf{d}_k) \le f(\mathbf{x}_k) + c\,\alpha\,\nabla f^\top \mathbf{d}_k$).

**Teória [M] (Nocedal a Wright, 2006):** na hladkej funkcii s kladne definitnou
Hessovou maticou konverguje superlineárne; na ostro konvexnej kvadratickej
funkcii s presným hľadaním na priamke skončí najviac po $n$ iteráciách.
Metóda je invariantná voči lineárnej transformácii, takže zlé podmienenie a
natočenie ju (na rozdiel od najstrmšieho zostupu) principiálne nebrzdí.

**Počet vyhodnotení pri `f20`:** gradient 21 (dopredný) až 40 (centrálny)
vyhodnotení + niekoľko na hľadanie na priamke, teda približne 100–160
iterácií v rozpočte 4000.

**Slabé stránky:** predpokladá hladkosť; pri šume alebo nehladkosti zlyhá;
je lokálna; chyba gradientu z diferencií obmedzuje dosiahnuteľnú presnosť
(blízko optima je gradient malý a relatívna chyba veľká) **[M]**.
**Vhodnosť:** `f20` – silný kandidát, **ak** je funkcia hladká **[H]**;
porovnanie s CMA-ES v E21. `f2000` – jeden gradient stojí 2001 vyhodnotení,
teda najviac ~9 gradientov – v takej podobe nevhodné.

---

## 9. Metódy pracujúce s podpriestormi (pre `f2000`)

**Motivácia [Z].** „Naslepo v nej nenájdete nič; oplatí sa najprv zistiť, na čom
záleží.“ Ak hodnota funkcie podstatne závisí iba od $k \ll n$ premenných (alebo
smerov), stačí optimalizovať v $k$-rozmernom podpriestore, kde je rozpočet na
dimenziu $B/k$ namiesto $B/n$.

### 9.1 Skríning citlivosti premenných (jedna premenná naraz)

Zvolíme základný bod $\mathbf{x}_0$ (napr. stred $\mathbf{0}$ alebo náhodný
bod) a pre každú premennú vypočítame efekt

$$
E_i = f(\mathbf{x}_0 + h_i \mathbf{e}_i) - f(\mathbf{x}_0), \qquad i = 1, \dots, n .
$$

To je $n$ vyhodnotení (všetky v jednej dávke). Premenné s veľkým $|E_i|$
považujeme za dôležité. Pri centrálnej verzii ($\pm h$) získame $2n$ hodnôt
a z nich aj odhad prvej aj druhej derivácie v smere $x_i$:

$$
g_i \approx \frac{f_+ - f_-}{2h}, \qquad c_i \approx \frac{f_+ - 2f_0 + f_-}{h^2}.
$$

**Riziká [M]:** efekt z jedného bodu môže byť náhodou malý (napr. ak je
$\mathbf{x}_0$ blízko minima v smere $x_i$ alebo je funkcia v tom smere
symetrická okolo $\mathbf{x}_0$) – preto dva základné body alebo veľké $h$;
skríning nezachytí interakcie medzi premennými.
Toto zovšeobecňujú *elementárne efekty* (Morrisova metóda) – opakovanie
skríningu z viacerých náhodných bodov.

### 9.2 Skupinový skríning

Premenné rozdelíme do skupín a meníme naraz celú skupinu. Ak sa hodnota
nezmení, žiadna premenná v skupine nie je dôležitá. Šetrí vyhodnotenia,
ale efekty sa môžu navzájom vyrušiť (rôzne znamienka) **[M]**.

### 9.3 Test aditivity (separability)

Pre dvojicu premenných $i, j$:

$$
I_{ij} = f(\mathbf{x}_0 + h\mathbf{e}_i + h\mathbf{e}_j) - f(\mathbf{x}_0 + h\mathbf{e}_i) - f(\mathbf{x}_0 + h\mathbf{e}_j) + f(\mathbf{x}_0).
$$

Pre separabilnú funkciu $f = \sum_i g_i(x_i)$ je $I_{ij} = 0$ (zmiešaná
druhá diferencia). Na vzorke dvojíc tak overíme H3′.

### 9.4 Optimalizácia v podpriestore

Po skríningu vyberieme množinu dôležitých premenných $S$, $|S| = k$, ostatné
zafixujeme (napr. na hodnotách najlepšieho bodu) a optimalizujeme

$$
\min_{\mathbf{x}_S} f(\mathbf{x}_S, \bar{\mathbf{x}}_{\bar S})
$$

metódou vhodnou pre $k$ rozmerov (napr. CMA-ES z časti 7.2, ktorá je pri
$k \le 100$ výpočtovo v poriadku). Alternatívou sú **náhodné podpriestory**
(*random embeddings*, Wang a kol., 2016): $\mathbf{x} = \mathbf{x}_0 + \mathbf{A}\mathbf{y}$
s náhodnou maticou $\mathbf{A} \in \mathbb{R}^{n \times k}$ – fungujú, ak je
efektívna dimenzia malá, aj keď nevieme, ktoré premenné sú dôležité.

### 9.5 Ak sú všetky premenné dôležité, ale funkcia je separabilná (H3′)

Potom sa dá každá premenná optimalizovať samostatne jednorozmernou metódou
(napr. parabolická interpolácia alebo zlatý rez, EAL 5). Pri 10 vyhodnoteniach
na premennú to je napr. 3–5 vyhodnotení na premennú v každom z dvoch kôl.
Pozor: aj tak sa mení vždy len jedna premenná naraz, takže nemôžeme využiť
dávkovanie naprieč premennými bez ďalších predpokladov.

**Náročnosť metód časti 9:** skríning $O(n)$ výpočtu na bod a $n$ až $2n$
vyhodnotení; optimalizácia v podpriestore $O(k^2)$ na kandidáta plus $O(n)$
na zostavenie bodu.

**Vhodnosť:** špecificky pre `f2000`; ktorá varianta, rozhodne diagnostický
experiment D03.

---

## 10. Lokálne vyhľadávanie s reštartmi a delenie rozpočtu

**Multištart [M].** Ak má lokálna metóda z náhodného štartu pravdepodobnosť
$q$ skončiť v globálnom minime, pri $r$ nezávislých štartoch je pravdepodobnosť
úspechu $1 - (1 - q)^r$. Ak štarty vyberáme z najlepších bodov prieskumu
(nie náhodne), $q$ sa zvyčajne zvýši, ale štarty už nie sú nezávislé.

**Výber štartov s rozptylom.** Aby sa dva štarty nespresňovali v tom istom
povodí, vyberáme najlepšie body prieskumu, ktoré sú od seba vzdialené aspoň
$d_{\min}$ (jednoduché „nikovanie“).

**Delenie rozpočtu.** Celkový rozpočet $B = B_{\text{prieskum}} + \sum_j B_{\text{spresnenie},j}$.
Veľký prieskum zvyšuje šancu nájsť správne povodie, ale zanechá málo na
spresnenie; pri zhode navyše rozhoduje rýchlosť **[Z]**. Optimálny pomer
je experimentálna otázka (E10).

**Reštart lokálnej metódy.** Spustí sa znova, keď stagnuje (napr. veľkosť
simplexu alebo $\sigma$ klesne pod prah, alebo sa za $T$ vyhodnotení nezlepší
najlepšia hodnota). Pri CMA-ES sa bežne používa reštart so zdvojnásobenou
populáciou (IPOP).

---

## 11. Ošetrenie hraníc

Body mimo $\Omega$ vyvolajú `ValueError` **[Z]**, takže ich nesmieme vyhodnotiť.

| Spôsob | Vzťah | Vlastnosti |
|---|---|---|
| orezanie | $x_i \leftarrow \min(\max(x_i, l_i), u_i)$ | jednoduché; veľa bodov môže skončiť presne na hranici |
| odraz | $x_i \leftarrow 2l_i - x_i$ (resp. $2u_i - x_i$) | zachová rozptyl vnútri oblasti |
| opakované vzorkovanie | vzorkovať znova, kým nie je bod vnútri | nemení rozdelenie vnútri, ale môže byť drahé pri veľkom $\sigma$ |

Keďže minimum leží vo vnútri $\Omega$ **[Z]**, v záverečnej fáze sa hranice
zvyčajne neuplatnia. Pri ES je dôležité, aby sa do aktualizácie stredu a
kovariancie použil bod, ktorý bol skutočne vyhodnotený (orezaný), inak sa
model rozíde s realitou **[M]**. Navrhujeme začať orezaním (je jednoduché a
bezpečné) a odraz otestovať, ak sa ukáže problém.

---

## 12. Súhrn vhodnosti metód

| Metóda | Rotácia | Výpočet na kandidáta | Dávkovanie | `f2` | `f20` | `f2000` |
|---|---|---|---|---|---|---|
| náhodné hľadanie | invariantná | $O(n)$ | áno | len prieskum | nevhodná | nevhodná |
| mriežka / LHS | – | $O(n)$ | áno | **prieskum** | inicializácia | inicializácia |
| súradnicové / Box–Wilson | **nie** | $O(n)$ | áno ($2n$) | spresnenie | nevhodná [M] | len pri H3′ |
| Nelder–Mead | čiastočne | $O(n)$ | nie | **spresnenie** | slabá [H] | nevhodná |
| CRS (EAL 5) | čiastočne | $O(n)$ | čiastočne | alternatíva [H] | slabá | nevhodná |
| GA (binárny) | **nie** | $O(nb)$ | áno | slabá | nevhodná | nevhodná |
| $(1+1)$-ES | invariantná | $O(n)$ | nie | referencia | referencia | **východisko** [H] |
| CMA-ES | invariantná | $O(n^2)$ | áno | možná | **hlavný kandidát** [H] | len v podpriestore |
| sep-CMA-ES | **nie** | $O(n)$ | áno | – | slabšia | **kandidát** [H] |
| FD + BFGS | invariantná | $O(n^2)$ | áno (gradient) | – | **kandidát** pri hladkosti [H] | nevhodná |
| skríning + podpriestor | – | $O(n)$ | áno | – | – | **kandidát pri H3** [H] |

---

## Literatúra (štandardné zdroje k metódam)

- Nelder, J. A., Mead, R. *A simplex method for function minimization.*
  The Computer Journal 7(4), 1965, s. 308–313.
- McKinnon, K. I. M. *Convergence of the Nelder–Mead simplex method to a
  nonstationary point.* SIAM Journal on Optimization 9(1), 1998, s. 148–158.
- Price, W. L. *A controlled random search procedure for global
  optimisation.* The Computer Journal 20(4), 1977, s. 367–370.
- Rechenberg, I. *Evolutionsstrategie.* Frommann-Holzboog, 1973.
- Hansen, N., Ostermeier, A. *Completely derandomized self-adaptation in
  evolution strategies.* Evolutionary Computation 9(2), 2001, s. 159–195.
- Hansen, N. *The CMA Evolution Strategy: A Tutorial.* arXiv:1604.00772, 2016.
- Ros, R., Hansen, N. *A simple modification in CMA-ES achieving linear time
  and space complexity.* PPSN X, 2008.
- Nocedal, J., Wright, S. J. *Numerical Optimization.* 2. vyd., Springer, 2006.
- Wang, Z. a kol. *Bayesian optimization in a billion dimensions via random
  embeddings.* Journal of Artificial Intelligence Research 55, 2016.
- Prednášky predmetu EAL/OMM uvedené na začiatku dokumentu.
