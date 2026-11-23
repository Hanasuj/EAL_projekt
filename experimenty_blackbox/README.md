# Experimenty k black-box súťaži

Skripty k diagnostikám a experimentom zapísaným v `blackbox/docs/experimenty.md`.
Sú zámerne **mimo** zložky `blackbox/`: používajú `matplotlib` a test
`blackbox/testy/test_importy.py` kontroluje každý `.py` súbor v `blackbox/`.

Spúšťajú sa z koreňa repozitára, napr.:

```bash
uv run python experimenty_blackbox/porovnanie.py        # E01–E03 (≈ 4 min)
uv run python experimenty_blackbox/d03_skrining_f2000.py
```

| Skript | Experiment |
|---|---|
| `d01_d02.py` | D01 mapa `f2`, D02 Hessova matica `f20` |
| `d03_skrining_f2000.py`, `d03b_podpriestor.py`, `d03c_slabe_premenne.py` | D03 štruktúra `f2000` |
| `e21_f20_rychly.py`, `e21b_bfgs_validacia.py`, `e21c_bfgs_start.py` | E21 metódy pre `f20` |
| `porovnanie.py` | E01, E02, E03 – referencie vs. `solve.py` |
| `ramec.py` | spoločný rámec (referencie, behy, ukazovatele) pre experimenty etáp 5–6 |
| `referencie.py`, `referencie.json` | R01 – referenčné hodnoty validačných inštancií |
| `e10_f2.py` | E10/E11 delenie rozpočtu pri `f2` |
| `e22_f20.py`, `e23_f20.py` | E22, E23 hľadanie na priamke a štarty pri `f20` |
| `e30_f2000.py`, `d04_rezidua_f2000.py` | E30, D04 varianty pre `f2000` |
| `e40_finalne.py` | E40 – `solve.py` po etape 6 |

Diagnostiky používajú rozpočty väčšie ako súťažné – slúžia iba na pochopenie
funkcií, nie ako súťažné behy.
