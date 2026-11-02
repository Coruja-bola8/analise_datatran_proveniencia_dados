"""Compara (ignorando final de linha) a versao do GitHub, que bate com a executada,
com a versao local. Grava saida/diff_versoes.txt."""
import difflib, sys
from pathlib import Path

clone = Path(sys.argv[1])
nomes = ["03_duplicatas.py", "04_ausentes.py", "05_padronizacao.py", "06_validacao_geo.py"]
saida = []
for n in nomes:
    a = (clone / n).read_text(encoding="utf-8").splitlines()
    b = Path(n).read_text(encoding="utf-8").splitlines()
    d = list(difflib.unified_diff(a, b, f"EXECUTADA/{n}", f"LOCAL/{n}", lineterm="", n=1))
    alt = sum(1 for l in d[2:] if l.startswith(("+", "-")))
    saida.append(f"##### {n}: {alt} linhas diferentes")
    saida.extend(d)
Path("saida").mkdir(exist_ok=True)
Path("saida/diff_versoes.txt").write_text("\n".join(saida), encoding="utf-8")
print("\n".join(l for l in saida if l.startswith("#####")))