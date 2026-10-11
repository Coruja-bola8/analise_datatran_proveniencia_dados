"""Etapa 1 (3.4): análise exploratória inicial, só leitura sobre raw.datatran_primario."""
import pandas as pd
from sqlalchemy import create_engine, text

from config import *
from prov import colunas_publicadas


def main():
    DIR_SAIDA.mkdir(exist_ok=True)
    eng = create_engine(DB_URL)
    pd.set_option("display.width", 200, "display.max_rows", 200)
    with eng.connect() as conn:
        cols = colunas_publicadas(conn)

        id_expr = 'count(DISTINCT r."id")' if "id" in cols else "NULL"
        por_ano = pd.read_sql(text(f"""
            SELECT a.ano, count(*) AS linhas, {id_expr} AS ids_distintos,
                   round(100.0 * count(*) FILTER (WHERE r.latitude_num IS NULL) / count(*), 2) AS pct_lat_nula,
                   round(100.0 * count(*) FILTER (WHERE r.longitude_num IS NULL) / count(*), 2) AS pct_lon_nula
            FROM raw.datatran_primario r JOIN prov.arquivo_origem a USING (id_arquivo)
            GROUP BY a.ano ORDER BY a.ano"""), conn)
        print("\n== Linhas e ausência de coordenadas por ano ==\n", por_ano)
        por_ano.to_csv(DIR_SAIDA / "diag_por_ano.csv", index=False)

        partes = ", ".join(f'count(*) FILTER (WHERE "{c}" IS NULL) AS "n_{c}", count(DISTINCT "{c}") AS "d_{c}"'
                           for c in cols)
        linha = pd.read_sql(text(f"SELECT count(*) AS total, {partes} FROM raw.datatran_primario"), conn).iloc[0]
        total = int(linha["total"])
        perfil = pd.DataFrame({
            "campo": cols,
            "nulos": [int(linha[f"n_{c}"]) for c in cols],
            "pct_nulos": [round(100 * int(linha[f"n_{c}"]) / total, 2) for c in cols],
            "distintos": [int(linha[f"d_{c}"]) for c in cols]})
        print(f"\n== Perfil por campo (total={total}, campos={len(cols)}) ==\n", perfil)
        perfil.to_csv(DIR_SAIDA / "diag_campos.csv", index=False)

        for c in [x for x in CAMPOS_PADRONIZAR if x in cols]:
            pd.read_sql(text(f'SELECT "{c}" AS valor, count(*) AS n FROM raw.datatran_primario '
                             f'GROUP BY 1 ORDER BY 2 DESC'), conn).to_csv(DIR_SAIDA / f"valores_{c}.csv", index=False)

        numericos = [c for c in ["km", "pessoas", "mortos", "feridos_leves", "feridos_graves", "ilesos",
                                 "ignorados", "feridos", "veiculos"] if c in cols]
        linhas = []
        for c in numericos:
            num = f"""CASE WHEN trim("{c}") ~ '^-?[0-9]+([.,][0-9]+)?$'
                      THEN replace(trim("{c}"), ',', '.')::numeric END"""
            r = conn.execute(text(f"""SELECT min(v), percentile_cont(0.25) WITHIN GROUP (ORDER BY v),
                percentile_cont(0.5) WITHIN GROUP (ORDER BY v), percentile_cont(0.75) WITHIN GROUP (ORDER BY v),
                percentile_cont(0.99) WITHIN GROUP (ORDER BY v), max(v)
                FROM (SELECT {num} AS v FROM raw.datatran_primario) t""")).one()
            linhas.append([c, *[None if x is None else float(x) for x in r]])
        q = pd.DataFrame(linhas, columns=["campo", "min", "q1", "mediana", "q3", "p99", "max"])
        q["iqr"] = q["q3"] - q["q1"]
        print("\n== Numéricos ==\n", q)
        q.to_csv(DIR_SAIDA / "diag_numericos.csv", index=False)


if __name__ == "__main__":
    main()
