"""Procura no historico do repositorio a versao de cada script cujo SHA-256
(final de linha normalizado para LF) bate com o registrado no banco."""
import hashlib, subprocess, sys

repo = sys.argv[1]
registrados = {"01_ingestao.py": "eedbe15474", "03_duplicatas.py": "d29c7887f5",
               "04_ausentes.py": "4416c68239", "05_padronizacao.py": "393778bc9d",
               "06_validacao_geo.py": "4e633c9c0f"}

def git(*args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, check=True).stdout

for nome, h in registrados.items():
    print(f"\n== {nome} (registrado: {h}) ==")
    log = git("log", "--format=%h|%ad|%s", "--date=short", "--", nome).decode("utf-8", "replace").splitlines()
    if not log:
        print("  nenhum commit encontrado")
    for linha in log:
        c, data, msg = linha.split("|", 2)
        try:
            b = git("show", f"{c}:{nome}")
        except subprocess.CalledProcessError:
            print(f"  {c} {data}  (arquivo ausente neste commit)  {msg}")
            continue
        sha = hashlib.sha256(b.replace(b"\r\n", b"\n")).hexdigest()[:10]
        fim = "CRLF" if b"\r\n" in b else "LF"
        print(f"  {c} {data} {sha} ({fim}) {msg}" + ("  <== BATE" if sha == h else ""))