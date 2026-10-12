"""Inspeção dos CSVs anuais antes de carregar no banco. Compara com os números do TCC."""
from pathlib import Path
import pandas as pd

PASTA = Path("dados/csv")
CHAVE_TCC = ["data_inversa", "horario", "km", "br", "uf"]
GRAO = ["id", "pesid", "id_veiculo", "ordem_tipo_acidente", "causa_acidente", "tipo_acidente"]

def ler(p):
    for enc in ("utf-8-sig", "latin-1"):
        try:
            return pd.read_csv(p, sep=";", dtype=str, encoding=enc), enc
        except UnicodeDecodeError:
            continue

linhas = []
for p in sorted(PASTA.glob("acidentes20*_todas_causas_tipos.csv")):
    ano = int("".join(ch for ch in p.stem if ch.isdigit())[:4])
    if not 2017 <= ano <= 2025:
        continue
    df, enc = ler(p)
    df.columns = [c.strip().lower() for c in df.columns]
    lat = df["latitude"].isna().mean() * 100 if "latitude" in df else None
    if ano == 2017:
        print("Colunas 2017:", list(df.columns))
    linhas.append({
        "ano": ano, "enc": enc, "linhas": len(df), "colunas": df.shape[1],
        "ids_distintos": df["id"].nunique(),
        "dup_linha_inteira": int(df.duplicated().sum()),
        "dup_chave_tcc": int(df.duplicated(CHAVE_TCC).sum()),
        "dup_grao": int(df.duplicated([c for c in GRAO if c in df]).sum()),
        "pct_lat_nula": round(lat, 2),
        "var_causa": df["causa_acidente"].nunique(), "var_tipo": df["tipo_acidente"].nunique(),
    })
res = pd.DataFrame(linhas)
pd.set_option("display.width", 250)
print(res.to_string(index=False))
print("\nTOTAL linhas:", res["linhas"].sum(), "| TCC: 1.512.340")
