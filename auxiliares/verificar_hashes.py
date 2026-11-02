"""Compara o hash dos scripts no disco com o registrado em prov.agente (somente leitura)."""
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text
from config import *
from prov import sha256_arquivo

eng = create_engine(DB_URL)
with eng.connect() as conn:
    ag = pd.read_sql(text("SELECT script, versao, sha256_codigo FROM prov.agente ORDER BY script"), conn)
ag["atual"] = [sha256_arquivo(s) if Path(s).exists() else None for s in ag["script"]]
ag["situacao"] = [("AUSENTE" if pd.isna(a) else "IGUAL" if a == r else "DIVERGENTE")
                  for a, r in zip(ag["atual"], ag["sha256_codigo"])]
ag["registrado_10"] = ag["sha256_codigo"].str[:10]
ag["atual_10"] = ag["atual"].str[:10]
print(ag[["script", "versao", "registrado_10", "atual_10", "situacao"]].to_string(index=False))