# Black-box soutěž

Logiku optimalizace pište sami: hotové optimalizační algoritmy
(`scipy.optimize`, `cma`, `optuna`, `nevergrad` …) v řešiči soutěže
povolené nejsou. Vyhodnocovací prostředí obsahuje `numpy` a standardní
knihovnu Pythonu; jinou obecnou knihovnu (bez hotového optimalizátoru)
přidáme, když o ni předem napíšete (viz pravidla soutěže).

Řešič pro společnou soutěž. **Vyhodnocuje se jen `solve.py`** – funkce
`solve(f, rng_seed)` v něm musí zůstat se stejnou signaturou; pomocné
moduly z této složky importovat smí, a to přímo (`import pomocne` pro
`blackbox/pomocne.py`) – složka `blackbox/` je v cestě při vyhodnocení,
v `spust_lokalne.py` i v testech, `sys.path` neupravujte. Funkce, rozhraní, rozpočty, limity,
bodování a žebříček popisují **pravidla soutěže na webu projektu**
(stránka `blackbox.html`); stručné shrnutí je v docstringu `solve.py`.

| Soubor | K čemu |
|---|---|
| `solve.py` | váš řešič; výchozí stav je náhodné hledání, které je potřeba porazit |
| `spust_lokalne.py` | vyzkoušení na veřejných vývojových seedech 1–5: tabulka, CSV a graf konvergence |
| `testy/` | kontrola rozpočtu, vráceného bodu, reprodukovatelnosti a importů (numpy, standardní knihovna a knihovny přidané na požádání) |
| `vystupy/` | grafy a tabulky z vašich experimentů |

Z kořene repozitáře:

```bash
uv run python blackbox/spust_lokalne.py               # vše, 3 seedy algoritmu
uv run python blackbox/spust_lokalne.py --funkce f20  # jen jedna funkce
uv run pytest blackbox                                # kontroly
```

`spust_lokalne.py` zapisuje do `blackbox/vystupy/` (vaše experimenty).
`spust_vse.py` v kořeni ho pouští jen jako rychlou zkoušku s přepínačem
`--bez-zapisu`, takže uložené výsledky experimentů nepřepíše.

Výsledky na vývojových seedech nejsou hodnocení – vyhodnocuje se na
tajných instancích.

## Strategie

*Doplňte: jakou strategii používáte pro jednotlivé funkce (f2, f20, f2000),
jak dělíte rozpočet mezi průzkum a zpřesnění, proč.*

## Experimenty

*Doplňte: aspoň jedno srovnání dvou nastavení nebo strategií na
vývojových seedech (tabulka nebo graf z `vystupy/`), a co z něj plyne.
Kde vaše strategie selhává?*
