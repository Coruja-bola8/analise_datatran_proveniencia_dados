"""Testa se a divergencia dos hashes se explica so pelo final de linha (somente leitura)."""
import hashlib
import sys
from pathlib import Path

pasta = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
registrados = {"01_ingestao.py": "eedbe15474", "03_duplicatas.py": "d29c7887f5",
               "04_ausentes.py": "4416c68239", "05_padronizacao.py": "393778bc9d",
               "06_validacao_geo.py": "4e633c9c0f"}
print(f"Pasta: {pasta.resolve()}")
for nome, h in registrados.items():
    p = pasta / nome
    if not p.exists():
        print(f"{nome:22} nao encontrado")
        continue
    b = p.read_bytes()
    lf = b.replace(b"\r\n", b"\n")
    var = {"como esta": b, "so LF": lf, "so CRLF": lf.replace(b"\n", b"\r\n")}
    achou = [k for k, v in var.items() if hashlib.sha256(v).hexdigest().startswith(h)]
    atual = hashlib.sha256(b).hexdigest()[:10]
    print(f"{nome:22} hash atual={atual}  bate com o registrado: {achou if achou else 'nenhuma variante'}")