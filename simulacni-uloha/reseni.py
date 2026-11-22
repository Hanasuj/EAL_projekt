"""Simulační úloha (S) – hlavní skript.

Spuštění z kořene repozitáře: uv run python simulacni-uloha/reseni.py

Cíl počítá simulátor od vyučujícího (black box, bez gradientu). Archiv
``data-Sxx.zip`` k vaší úloze rozbalte přímo do této složky:
``simulator.py`` patří vedle ``reseni.py``, data do ``simulacni-uloha/data/``.
Simulátor neupravujte, test řešení přepočítá právě jím.

Kostra drží tři věci oddělené:

(a) ``vytvor_ucel`` – účelová funkce, kterou vidí optimalizátor. Jen ona se
    počítá do rozpočtu (``Pocitadlo``) a smí používat jen to, co zadání
    dovoluje pro hledání (trénovací data, seedy hledání, pokuta …).
(b) ``kontrola`` – nezávislé ověření hotového výsledku: přepočet hodnoty
    (kontrolní seedy, testovací data), přípustnost, případně pravda „jen
    pro vyhodnocení“. Optimalizátor ji nevidí a do rozpočtu se nepočítá.
(c) srovnání přes seedy (medián a kvartily, ne nejlepší běh) a uložení
    jednoho řešení, které vybere předem stanovené pravidlo ``vyber`` –
    nikdy podle výsledku kontroly.

Víc účelů (S08 parsimonie a věrohodnost) nebo rozpočet na instanci
(na obrázek, na text): ``vytvor_ucel`` vrátí slovník {klíč: funkce},
metoda volá ``f["klic"](x)`` a ``Pocitadlo`` vede nejlepší hodnoty
a průběh pro každý klíč zvlášť, takže se škály nesměšují. ``ROZPOCET``
je pak číslo (sdílené všemi klíči), nebo slovník {klíč: rozpočet}.

Řešení nemusí být vektor čísel: může to být permutace, strom, řetězec,
slovník … Kostra s ním zachází jako s neprůhledným objektem; jak se uloží
a načte, určují funkce ``uloz`` a ``nacti``.

Metodu volíte sami: vlastní implementace, nebo hotové knihovny
(``cma``, ``optuna``, ``scipy.optimize`` …). Konvence: cíl se
**minimalizuje** (maximalizaci otočte znaménkem).
"""

import copy
import csv
import json
import sys
from pathlib import Path

import numpy as np

ZDE = Path(__file__).resolve().parent
VYSTUPY = ZDE / "vystupy"
RESENI = VYSTUPY / "reseni.json"
sys.path.insert(0, str(ZDE))  # simulator.py ze stejné složky i při importu z testu

# Rozpočet jednoho běhu v jednotkách úlohy podle zadání (běhy simulace,
# hry, jamky, sektor-vyhodnocení …); kolik jednotek stojí jedno volání
# účelové funkce, určuje funkce ``cena``.
ROZPOCET = 1000
SEEDY = list(range(10))
TOL = 1e-9  # kolik porušení omezení se ještě bere jako přípustné


def nacti_simulator():
    """Vrátí modul simulator.py (a případně data, která potřebuje)."""
    if not (ZDE / "simulator.py").exists():
        raise FileNotFoundError("rozbalte archiv úlohy do simulacni-uloha/ (chybí simulator.py)")
    import simulator

    return simulator


# ---------------------------------------------------------------- (a) co vidí optimalizátor

def vytvor_ucel(sim, seed):
    """Vrátí účelovou funkci pro jeden běh optimalizace (menší = lepší).

    Smí používat jen to, co zadání dovoluje při hledání: trénovací data,
    simulace se seedy odvozenými z ``seed`` (ne s kontrolními), případně
    pokutu za porušení omezení. Pravdu „jen pro vyhodnocení“ sem nedávejte.
    Stav jednoho běhu (např. objekt laboratoře se šumem) držte uvnitř.

    Vrácená funkce dostane řešení (a případně další argumenty, které jí
    předá vaše metoda) a vrátí číslo. U dávky (víc řešení najednou, např.
    destička receptů) smí vrátit pole hodnot, jednu pro každé řešení.
    Víc účelů nebo instancí: vraťte slovník {klíč: funkce}.
    """
    def ucel(x):
        raise NotImplementedError("doplňte: zavolejte simulátor podle zadání")

    return ucel


def cena(x, *args, klic=None, **kwargs):
    """Kolik jednotek rozpočtu stojí jedno volání účelové funkce s těmito
    argumenty (např. počet her, jamek v dávce, sektorů); ``klic`` je klíč
    účelu ze slovníku (jinak None). Výchozí stav: 1."""
    return 1


# ---------------------------------------------------------------- (b) nezávislá kontrola

def kontrola(x, sim):
    """Ověří hotové řešení mimo rozpočet; optimalizátor ji nevidí.

    Vrací slovník s aspoň dvěma čísly:
      ``hodnota``  – přepočet cíle tak, jak ho zadání hodnotí (kontrolní
                     seedy, testovací data …), menší = lepší,
      ``poruseni`` – míra porušení mezí a omezení (0 = přípustné).
    Další položky (např. ``pravda`` jen pro vyhodnocení) přidat smíte.
    Musí být deterministická (pevné seedy), test ji přepočítá.
    """
    raise NotImplementedError("doplňte: přepočet a přípustnost podle zadání")


# ---------------------------------------------------------------- rozpočet

class RozpocetVycerpan(RuntimeError):
    pass


class Pocitadlo:
    """Obal kolem účelové funkce: počítá spotřebu rozpočtu v jednotkách
    úlohy, pamatuje si průběh (pro graf konvergence), nejlepší bod podle
    hodnoty, kterou vidí optimalizátor, a řešení, které metoda zvolila.

    ``fce`` je jedna funkce (volání ``f(x)``), nebo slovník {klíč: funkce}
    (volání ``f["klic"](x)``); nejlepší bod a průběh se vedou pro každý
    klíč zvlášť (jedna funkce má klíč None). ``rozpocet`` je číslo
    (společné pro všechny klíče), nebo slovník {klíč: rozpočet}.
    S řešením nic nepředpokládá (ne ``np.asarray``), nejlepší bod ukládá
    jako hlubokou kopii a další argumenty volání předá dál do účelové
    funkce i do ``cena``.
    """

    def __init__(self, fce, rozpocet, cena=lambda x, *a, **k: 1):
        self.fce, self.rozpocet, self.cena = fce, rozpocet, cena
        self.spotreba = {}    # klíč -> spotřebované jednotky
        self.prubeh = {}      # klíč -> [(spotřebováno celkem, nejlepší hodnota dosud)]
        self.nejlepsi = {}    # klíč -> (nejlepší hodnota, řešení)
        self.zvolene, self.zvolena_hodnota = None, np.nan

    @property
    def spotrebovano(self):
        return sum(self.spotreba.values())

    @property
    def nejlepsi_y(self):  # jen pro jednu funkci (klíč None)
        return self.nejlepsi.get(None, (np.inf, None))[0]

    @property
    def nejlepsi_x(self):
        return self.nejlepsi.get(None, (np.inf, None))[1]

    def zvol(self, x, hodnota=None):
        """Metoda tím hlásí řešení, za kterým teď stojí, a svůj odhad jeho
        hodnoty (menší = lepší; podle něj porovnává běhy ``vyber``). Když
        rozpočet dojde uprostřed běhu, uloží se poslední zvolené."""
        if hodnota is None:
            hodnota = self.nejlepsi_y if x is self.nejlepsi_x else np.nan
        self.zvolene, self.zvolena_hodnota = x, float(hodnota)

    def __getitem__(self, klic):
        return lambda x, *args, **kwargs: self._volej(klic, x, *args, **kwargs)

    def __call__(self, x, *args, **kwargs):
        return self._volej(None, x, *args, **kwargs)

    def _volej(self, klic, x, *args, **kwargs):
        fce = self.fce if klic is None else self.fce[klic]
        c = self.cena(x, *args, klic=klic, **kwargs)
        zvlast = isinstance(self.rozpocet, dict)
        limit = self.rozpocet[klic] if zvlast else self.rozpocet
        if (self.spotreba.get(klic, 0) if zvlast else self.spotrebovano) + c > limit:
            raise RozpocetVycerpan(f"vyčerpán rozpočet {limit}" + (f" pro {klic}" if zvlast else ""))
        self.spotreba[klic] = self.spotreba.get(klic, 0) + c
        y = fce(x, *args, **kwargs)
        # jedno řešení -> číslo; dávka (posloupnost řešení) -> pole hodnot
        pary = [(x, y)] if np.ndim(y) == 0 else zip(x, np.ravel(y))
        for xi, yi in pary:
            if float(yi) < self.nejlepsi.get(klic, (np.inf,))[0]:
                self.nejlepsi[klic] = (float(yi), copy.deepcopy(xi))
        self.prubeh.setdefault(klic, []).append(
            (self.spotrebovano, self.nejlepsi.get(klic, (np.inf,))[0]))
        return y


# ---------------------------------------------------------------- metody

def optimalizuj(f, rozpocet, seed):
    """Vaše metoda. Smí volat jen ``f(x)`` (nebo ``f["klic"](x)``), celkem
    nejvýš za ``rozpocet``, veškerá náhodnost z ``seed``. Vrátí řešení, za
    kterým stojí; průběžně ho hlaste ``f.zvol(x, hodnota)``, aby platilo
    i po výjimce ``RozpocetVycerpan`` uprostřed běhu. U zašuměné úlohy to
    nemusí být nejšťastnější měření (``f.nejlepsi_x``), ale třeba bod
    s nejlepším průměrem opakování. Metod může být víc (viz METODY)."""
    raise NotImplementedError("doplňte vlastní metodu")


# jméno -> funkce se signaturou (f, rozpocet, seed); první je hlavní metoda
METODY = {"moje_metoda": optimalizuj}


# ---------------------------------------------------------------- (c) srovnání a výběr

def vyber(behy):
    """Předem stanovené pravidlo, které řešení se uloží. Nesmí se dívat na
    výsledek kontroly (to by byl výběr podle pravdy). Výchozí stav: běh
    hlavní metody s mediánovým odhadem ``ucel`` (hodnota ze ``f.zvol``,
    tu znal optimalizátor; běh bez odhadu se řadí na konec)."""
    hlavni = sorted((b for b in behy if b["metoda"] == next(iter(METODY))),
                    key=lambda b: np.nan_to_num(b["ucel"], nan=np.inf))
    return hlavni[(len(hlavni) - 1) // 2]


def _do_json(x):
    if isinstance(x, np.ndarray):
        return x.tolist()
    if isinstance(x, np.generic):
        return x.item()
    if isinstance(x, (list, tuple)):
        return [_do_json(v) for v in x]
    if isinstance(x, dict):
        return {str(k): _do_json(v) for k, v in x.items()}
    return x


def uloz(x, cesta, sim, **info):
    """Uloží řešení a údaje o něm. Výchozí stav: JSON, zvládne čísla,
    řetězce, seznamy, n-tice, slovníky a numpy pole. Jiné řešení (strom,
    objekt) převeďte, nebo funkci přepište – spolu s ``nacti``. ``sim``
    je simulátor (kontext, např. jména taxonů pro Newick)."""
    zaznam = dict(reseni=_do_json(x), **{k: _do_json(v) for k, v in info.items()})
    Path(cesta).write_text(json.dumps(zaznam, indent=2, ensure_ascii=False))


def nacti(cesta, sim):
    """Opak ``uloz``: vrátí (řešení, údaje). Řešení musí přijmout ``kontrola``
    (seznam z JSON si tam případně převeďte zpět na pole nebo strom)."""
    zaznam = json.loads(Path(cesta).read_text())
    return zaznam.pop("reseni"), zaznam


def kvartily(hodnoty):
    """Medián a kvartily; běh bez řešení (inf) je horší než všechny ostatní."""
    with np.errstate(invalid="ignore"):  # inf - inf při samých neúspěšných bězích
        q1, med, q3 = np.percentile(hodnoty, [25, 50, 75])
    return med, q1, q3


def main():
    VYSTUPY.mkdir(exist_ok=True)
    sim = nacti_simulator()
    behy = []
    for jmeno, metoda in METODY.items():
        for seed in SEEDY:
            f = Pocitadlo(vytvor_ucel(sim, seed), ROZPOCET, cena=cena)
            try:
                vraceno = metoda(f, ROZPOCET, seed)
                if vraceno is not None and vraceno is not f.zvolene:
                    f.zvol(vraceno)
            except RozpocetVycerpan:  # běh platí, bere se poslední f.zvol
                pass
            x = f.zvolene
            if x is None:  # metoda nic nezvolila: běh se počítá jako neúspěšný
                k = dict(hodnota=np.inf, poruseni=np.inf)
            else:
                k = kontrola(x, sim)  # mimo rozpočet, metoda ji neviděla
            behy.append(dict(metoda=jmeno, seed=seed, spotrebovano=f.spotrebovano,
                             ucel=f.zvolena_hodnota, x=x, prubeh=f.prubeh, kontrola=k,
                             hodnota=k["hodnota"], poruseni=k["poruseni"]))
            print(f"{jmeno:>15} seed {seed}: účel {f.zvolena_hodnota:.6g}, kontrola {k['hodnota']:.6g}, "
                  f"porušení {k['poruseni']:.3g} (spotřeba {f.spotrebovano})"
                  + ("  BEZ ŘEŠENÍ: metoda nic nevrátila ani nezvolila" if x is None else ""))

    # Souhrn přes seedy: medián a kvartily, ne nejlepší běh.
    with open(VYSTUPY / "souhrn.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["metoda", "behu", "pripustnych", "kontrola_median", "kontrola_q1",
                    "kontrola_q3", "ucel_median"])
        for jmeno in METODY:
            mb = [b for b in behy if b["metoda"] == jmeno]
            med, q1, q3 = kvartily([b["hodnota"] for b in mb])
            ok = sum(b["poruseni"] <= TOL for b in mb)
            w.writerow([jmeno, len(mb), ok, med, q1, q3, kvartily([b["ucel"] for b in mb])[0]])
            print(f"{jmeno:>15}: kontrola medián {med:.6g} (kvartily {q1:.6g} až {q3:.6g}), "
                  f"přípustných {ok}/{len(mb)}")
    # sem patří graf konvergence (b["prubeh"][klíč]) a další tabulky srovnání

    b = vyber(behy)
    if b["x"] is None:
        sys.exit("žádný běh hlavní metody nemá řešení, není co uložit")
    uloz(b["x"], RESENI, sim, metoda=b["metoda"], seed=b["seed"], rozpocet=ROZPOCET,
         kontrola=b["kontrola"])
    print(f"Uloženo: {b['metoda']}, seed {b['seed']} -> {RESENI}")


if __name__ == "__main__":
    main()
