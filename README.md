# Projekt z optimalizace 2026 – tým *doplňte název*

| Člen | Login |
|---|---|
| *Hana Sujová* | *247305* |
| *Karolína Holotová* | *247242* |


## Struktura

| Složka | Obsah |
|---|---|
| `model-uloha/` | modelová úloha (M, přesný model LP/QP/MILP a řešič): *doplňte ID a název* |
| `simulacni-uloha/` | simulační úloha (S, black box se simulátorem): *doplňte ID a název* |
| `blackbox/` | řešič společné black-box soutěže (`blackbox/solve.py`) |

```
model-uloha/       reseni.py, README.md, data/, vystupy/, testy/test_model.py
simulacni-uloha/   reseni.py, simulator.py a data/ (z archivu úlohy), README.md,
                   vystupy/, testy/test_simulace.py
blackbox/          solve.py, spust_lokalne.py, README.md, vystupy/, testy/
```

Každá složka má vlastní `README.md` s modelem, výsledky a interpretací.

## Spuštění

Potřebujete [uv](https://docs.astral.sh/uv/). Na čistém stroji:

```bash
uv sync
uv run python spust_vse.py      # obě úlohy + lokální test black boxu
uv run pytest                   # všechny kontroly
```

Vše, co je v README modelové a simulační úlohy uvedeno jako výsledek,
musí tento příkaz znovu vytvořit (tabulky a grafy v `*/vystupy/`).
`spust_vse.py` jde spustit z libovolného adresáře. Black box v něm jen
rychle vyzkouší, že `blackbox/solve.py` běží, a nic neukládá; experimenty
pro `blackbox/README.md` pouštějte zvlášť přes
`uv run python blackbox/spust_lokalne.py` (zapisuje do `blackbox/vystupy/`).

V nevyplněné šabloně `spust_vse.py` u obou úloh záměrně skončí chybou
(`NotImplementedError`, u simulační úlohy nejdřív chybějící `simulator.py`):
kostru je potřeba doplnit.
`uv run pytest` s prázdnou kostrou neselže, ale zelená není: testy, které
máte doplnit, se hlásí jako přeskočené („doplňte test chybného řešení“),
a test simulační úlohy se přeskočí, dokud ve složce není `simulator.py`
a uložené řešení `vystupy/reseni.json`.

### Modul black boxu

Modul `omm-blackbox` se instaluje sám při `uv sync` z wheelu ve vydání
[blackbox-v0.1.0](https://github.com/tomasvicar/OMM-public/releases/tag/blackbox-v0.1.0).
Wheely jsou pro Linux (x86_64, aarch64), Windows (64bit) a macOS (Apple
Silicon i Intel); `uv` vybere ten pro váš systém. Kdyby instalace na vašem
systému selhala, napište vyučujícímu.

### Vlastní knihovny

Prostředí si upravte, jak potřebujete: další knihovnu přidáte příkazem
`uv add <balík>` (zapíše se do `pyproject.toml` i `uv.lock`, commitněte
obojí). Šablona už obsahuje i hotové optimalizátory `cma` (CMA-ES)
a `optuna`; v simulační úloze je smíte použít. Výjimkou je **řešič
black-box soutěže** v `blackbox/`: tam hotové optimalizační algoritmy (`scipy.optimize`, `cma`, `optuna`, …)
povolené nejsou, viz pravidla soutěže.

## Co patří do repozitáře

- **`uv.lock`** – vznikne při `uv sync`; commitněte ho, aby se na čistém
  stroji nainstalovaly přesně stejné verze knihoven.
- **Data úloh** v `model-uloha/data/` a `simulacni-uloha/data/` a simulátor
  `simulacni-uloha/simulator.py` (z archivu úlohy) – commitněte je (jsou malá), aby
  `spust_vse.py` prošel bez dalšího stahování.
- **Vybrané řešení simulační úlohy** (výchozí `simulacni-uloha/vystupy/reseni.json`,
  zapíše ho `reseni.py`) – test ho přepočítá simulátorem.
- Kód, testy, README složek a výstupy, na které se v README odkazujete.
- Nepatří sem `.venv/` ani mezivýsledky (hlídá `.gitignore`).

Složky úloh mají v názvu pomlčku, takže nejsou balíky: testy načítají
`reseni.py` ze souboru (funkce `nacti_reseni` v `testy/`). Samotné
`import reseni` nepoužívejte – obě úlohy mají soubor `reseni.py` a test by
mohl tiše testovat kód druhé úlohy.

## Použití AI

*Doplňte: s čím vám AI pomohla (kód, formulace modelu, texty, ladění) a
jak jste její výstupy ověřili. Použití AI je povolené (očekává se i použití AI agentů); obhajujete
společně, ale každý člen týmu musí rozumět všem třem částem.*
