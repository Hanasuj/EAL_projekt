# Modelová úloha (M)

**Úloha:** *doplňte ID a název z nabídky (např. „Mxx – název úlohy“)*

Spuštění: `uv run python model-uloha/reseni.py` (vytvoří vše v `model-uloha/vystupy/`),
kontroly: `uv run pytest model-uloha`.

## Model

*Proměnné (co znamenají, jednotky, které jsou celočíselné nebo binární),
účelová funkce, omezení. Nejdřív základní model, pak upravený model
s novým požadavkem. Jaký je to typ úlohy (LP, QP, MILP) a co z toho plyne
pro řešení: proč je nalezené řešení optimální, ne jen dobré.*

## Výsledky

*Tabulka a graf: základní vs. upravený model. Čísla musí odpovídat tomu, co
vypíše `reseni.py`. U MILP uveďte i mezeru optimality, kterou řešič
dosáhl.*

## Interpretace

*Co nový požadavek stál v původním cíli a co přinesl? Co by se stalo, kdyby
se hotové řešení základního modelu jen ořízlo / zaokrouhlilo / opravilo
ručně? Vlastní experiment a jeho závěr.*

## Kontroly

*Jak ověřujete, že řešení je přípustné a správné nezávisle na stavu
řešiče (CVXPY, `scipy.optimize.milp`): přepočet cíle a omezení z čísel,
celočíselnost, test, který chybné řešení odmítne.*
