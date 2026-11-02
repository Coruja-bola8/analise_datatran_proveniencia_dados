import difflib, subprocess
from pathlib import Path

repo = r"C:\Users\User\AppData\Local\Temp\repo_teste"
executada = subprocess.run(["git", "-C", repo, "show", "e049ec8:01_ingestao.py"],
                           capture_output=True, check=True).stdout.decode("utf-8").splitlines()
local = Path(r"C:\Users\User\Desktop\datatran_prov\01_ingestao.py").read_text(encoding="utf-8").splitlines()
d = list(difflib.unified_diff(executada, local, "EXECUTADA/01_ingestao.py", "LOCAL/01_ingestao.py", lineterm="", n=1))
Path(r"C:\Users\User\Desktop\datatran_prov\saida\diff_01.txt").write_text("\n".join(d), encoding="utf-8")
print(len(d), "linhas de diff")