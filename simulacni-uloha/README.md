# Simulační úloha (S)

**Úloha:** *doplňte ID a název z nabídky (např. „Sxx – název úlohy“)*

Spuštění: `uv run python simulacni-uloha/reseni.py` (vytvoří vše v
`simulacni-uloha/vystupy/`, vybrané řešení do `vystupy/reseni.json`),
kontroly: `uv run pytest simulacni-uloha`.

Archiv `data-Sxx.zip` z nabídky rozbalte přímo do této složky:
`simulator.py` patří vedle `reseni.py`, data do `data/`. Simulátor ani
data neupravujte. Test uložené řešení znovu ověří (`kontrola`)
a zkontroluje přípustnost.

Metodu volíte sami. Smíte ji napsat, nebo použít hotové knihovny (`cma`,
`optuna`, `scipy.optimize` …); zákaz hotových optimalizátorů platí jen
pro řešič black-box soutěže.

Kostra v `reseni.py` drží odděleně:

- **`vytvor_ucel`** – účelová funkce, kterou vidí optimalizátor (pro každý
  běh nová, se stavem běhu uvnitř). Jen ta se počítá do rozpočtu.
- **`kontrola`** – nezávislé ověření hotového výsledku (přepočet na
  kontrolních seedech nebo testovacích datech, přípustnost, případně pravda
  „jen pro vyhodnocení“). Optimalizátor ji nevidí.
- **`vyber`** – předem stanovené pravidlo, které řešení se uloží; nesmí se
  rozhodovat podle kontroly.

**Rozpočet** (`ROZPOCET`) je v jednotkách, které určuje zadání vaší
úlohy (běhy simulace, hry, jamky, sektor-vyhodnocení …); kolik jednotek
stojí jedno volání účelové funkce, vrací funkce `cena`. Řešení nemusí
být vektor čísel (permutace, strom, klíč jako řetězec …): kostra s ním zachází jako
s neprůhledným objektem a ukládá ho funkcí `uloz` (výchozí JSON),
kterou si spolu s `nacti` upravte podle svého řešení.

Metoda vrací řešení, za kterým stojí, a průběžně ho hlásí
`f.zvol(x, hodnota)`: když rozpočet dojde uprostřed běhu, uloží se
poslední zvolené. U zašuměné úlohy to nemá být nejšťastnější měření
(`f.nejlepsi_x`), ale třeba bod s nejlepším průměrem opakování.

**Víc účelů nebo rozpočet na instanci.** Když úloha vyhodnocuje víc
funkcemi (parsimonie a věrohodnost, dva cíle) nebo má rozpočet na každý
obrázek či text zvlášť, vraťte z `vytvor_ucel` slovník
`{klíč: funkce}`. Metoda pak volá `f["klic"](x)` a `Pocitadlo` vede
nejlepší hodnotu a průběh pro každý klíč zvlášť, takže se škály
nesměšují; cenu podle klíče určí `cena(x, klic=…)`. `ROZPOCET` je číslo
(jeden společný rozpočet, např. 20 000 jednotek pro parsimonie
i věrohodnosti) nebo slovník `{klíč: rozpočet}` (např. 2000 dotazů na
každý obrázek). Které řešení metoda nakonec zvolí, rozhoduje ona
(`f.zvol`); `uloz` a `nacti` dostávají i simulátor, takže umí třeba
převést strom na Newick se jmény taxonů.

> **Srovnání metod je férové jen při stejném rozpočtu a na víc seedech.**
> Uvádějte medián a kvartily přes seedy, ne jeden nejlepší běh.

## Úloha a proměnné

*Co se optimalizuje (proměnné, jednotky, meze, celočíselné části), jaký je
cíl a jaká omezení. Jak omezení řešíte (pokuta, oprava bodu, jiné
proměnné) a proč.*

## Metody a nastavení

*Které metody srovnáváte, s jakým rozpočtem vyhodnocení a kolika seedy.
Proč právě ty: co o krajině víte (šum, lokální minima, plató, rozměr)?*

## Výsledky

*Tabulka (medián a kvartily přes seedy, `vystupy/souhrn.csv`) a graf
konvergence (hodnota vs. spotřebovaný rozpočet) pro všechny metody a seedy. Čísla musí odpovídat tomu, co vypíše `reseni.py`.*

## Interpretace

*Co nejlepší řešení znamená věcně? Je robustní (jiné seedy, jiné instance,
šum)? Kde metoda selhává? Vlastní experiment a jeho závěr.*

## Kontroly

*Jak ověřujete, že řešení je přípustné a že výsledek není artefakt jednoho
běhu nebo chyby v účelové funkci.*
