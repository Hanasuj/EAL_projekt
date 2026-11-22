"""Spustí celý projekt jedním příkazem: uv run python spust_vse.py

Funguje z libovolného adresáře (kroky běží z kořene repozitáře). Black box
se tu jen rychle vyzkouší (jeden seed, nic se neukládá); experimenty
do blackbox/vystupy/ pouštějte zvlášť: uv run python blackbox/spust_lokalne.py
"""

import os
import subprocess
import sys
from pathlib import Path

KOREN = Path(__file__).resolve().parent

# Na Windows má výstup přesměrovaný do souboru nebo roury (> log.txt, CI)
# kódování cp1252 bez č, ř, ě…, takže by print s češtinou spadl. Proto UTF-8
# tady i v pouštěných skriptech.
sys.stdout.reconfigure(encoding="utf-8")
PROSTREDI = {**os.environ, "PYTHONIOENCODING": "utf-8"}

KROKY = [
    ["model-uloha/reseni.py"],
    ["simulacni-uloha/reseni.py"],
    ["blackbox/spust_lokalne.py", "--opakovani", "1", "--bez-zapisu"],
]

selhalo = []
for krok in KROKY:
    print(f"\n######## {' '.join(krok)} ########", flush=True)
    if subprocess.run([sys.executable, str(KOREN / krok[0]), *krok[1:]], cwd=KOREN, env=PROSTREDI).returncode != 0:
        selhalo.append(krok[0])

if selhalo:
    sys.exit(f"\nSelhalo: {', '.join(selhalo)}")
print("\nVše proběhlo.")
