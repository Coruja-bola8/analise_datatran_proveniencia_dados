"""Consultas de apoio ao item 1 da rubrica (somente leitura)."""
from itertools import count

import pandas as pd
from sqlalchemy import create_engine, text
from pathlib import Path
from config import DB_URL, DIR_SAIDA

CONSULTAS = {
    "A1_sem_geom_por_br_nula": """
        SELECT (aux.br_int(c.br) IS NULL) AS sem_br, count(*) AS linhas,
               count(DISTINCT c.id) AS acidentes
        FROM clean.geo_linha g JOIN clean.datatran c USING (rid)
        WHERE g.validacao_geo = 'OK_SEM_GEOM_RODOVIA'
        GROUP BY 1""",
    "A2_sem_geom_por_br": """
        SELECT aux.br_int(c.br) AS br, count(*) AS linhas
        FROM clean.geo_linha g JOIN clean.datatran c USING (rid)
        WHERE g.validacao_geo = 'OK_SEM_GEOM_RODOVIA' AND aux.br_int(c.br) IS NOT NULL
        GROUP BY 1 ORDER BY 2 DESC""",
    "B_dist_rodovia_top12": """
        SELECT uf, br, count(*) AS acidentes
        FROM clean.acidente WHERE validacao_geo = 'DIST_RODOVIA'
        GROUP BY 1, 2 ORDER BY 3 DESC LIMIT 12""",
    "C_fusoes_por_campo": """
        SELECT campo, count(*) AS pares,
               count(*) FILTER (WHERE fusao) AS pares_fusao,
               sum(n_celulas) FILTER (WHERE fusao) AS celulas_fusao
        FROM prov.transformacao_valor GROUP BY 1 ORDER BY 1""",
    "regitro_modificacao": """
        SELECT pg_size_pretty(pg_total_relation_size('prov.modificacao'));"""
}

DIR_SAIDA.mkdir(exist_ok=True)

# Conecta o Banco de Dados usando DB_URL diretamente
eng = create_engine(DB_URL)
with eng.connect() as conn:
    for nome, sql in CONSULTAS.items():
        df = pd.read_sql(text(sql), conn)
        print(f"\n=== {nome} ===")
        print(df.to_string(index=False))
        df.to_csv(DIR_SAIDA / f"item1_{nome}.csv", index=False)

