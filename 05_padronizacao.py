"""Etapa 4 (v3): padronização. UPPER+TRIM+sem acento+espaços colapsados; campos-conjunto (tracado_via) têm os
componentes ';' normalizados e ORDENADOS; mapa canônico opcional em mapas/<campo>.csv.

REGISTRO DE PROVENIÊNCIA (granularidade escolhida, ver Simmhan et al. 2005):
 - por VALOR: uma linha em prov.transformacao_valor para cada par distinto (campo, valor_original -> valor_novo),
   com o número de células afetadas. Basta para reverter quando a transformação é injetiva;
 - por LINHA: quando a transformação FUNDE valores diferentes em um só (perda de informação), cada linha afetada
   também é registrada em prov.modificacao com o valor original (regra 'padronizacao_com_fusao').
Assim a reversibilidade é mantida sem gravar dezenas de milhões de linhas de log."""
import json
import time
import pandas as pd
from sqlalchemy import create_engine, text
from config import *
from params import *
from prov import abrir_atividade, fechar_atividade, colunas_publicadas, exigir_nao_executada

ETAPA = "E4_padronizacao"
ESPACOS = r"regexp_replace(upper(unaccent(trim({x}))), '\s+', ' ', 'g')"
DDL = """
CREATE TABLE IF NOT EXISTS prov.transformacao_valor (
  id_transf      bigserial PRIMARY KEY,
  id_atividade   int NOT NULL REFERENCES prov.atividade,
  campo          text NOT NULL,
  valor_original text NOT NULL,
  valor_novo     text NOT NULL,
  regra          text NOT NULL,
  n_celulas      bigint NOT NULL,
  fusao          boolean NOT NULL      -- true: mais de um valor original gera este valor novo
);
CREATE INDEX IF NOT EXISTS ix_tv_campo ON prov.transformacao_valor (campo)"""


def expr(col_sql, conjunto):
    if conjunto:
        n = ESPACOS.format(x="x")
        return f"(SELECT string_agg({n}, ';' ORDER BY {n}) FROM unnest(string_to_array({col_sql}, ';')) AS x)"
    return ESPACOS.format(x=col_sql)


def main():
    DIR_SAIDA.mkdir(exist_ok=True)
    t0 = time.time()
    eng = create_engine(DB_URL)
    with eng.begin() as conn:
        exigir_nao_executada(conn, ETAPA)
        for stmt in DDL.split(";"):
            if stmt.strip():
                conn.execute(text(stmt))
        cols = colunas_publicadas(conn)
        campos = [c for c in CAMPOS_PADRONIZAR if c in cols]
        params = {"campos": campos, "conjunto": CAMPOS_CONJUNTO,
                  "regra": "upper(unaccent(trim())) + espaços colapsados (+ ordenação de componentes) + mapa canônico",
                  "registro": "por valor (prov.transformacao_valor) + por linha nas fusões"}
        ida = abrir_atividade(conn, ETAPA, __file__, params, entrada="clean.datatran", saida="clean.datatran")
        resumo, usados = [], []

        for c in campos:
            conj = c in CAMPOS_CONJUNTO
            conn.execute(text("DROP TABLE IF EXISTS _v"))
            conn.execute(text(f'CREATE TEMP TABLE _v AS SELECT "{c}" AS orig, count(*) AS n '
                              f'FROM clean.datatran WHERE "{c}" IS NOT NULL GROUP BY 1'))
            conn.execute(text("ALTER TABLE _v ADD COLUMN norm text, ADD COLUMN novo text, ADD COLUMN fusao boolean"))
            conn.execute(text(f"UPDATE _v SET norm = {expr('orig', conj)}"))

            conn.execute(text("DROP TABLE IF EXISTS _map"))
            conn.execute(text("CREATE TEMP TABLE _map (variante text PRIMARY KEY, canonico text NOT NULL)"))
            arq = DIR_MAPAS / f"{c}.csv"
            if arq.exists():
                m = pd.read_csv(arq, dtype=str)[["variante", "canonico"]].dropna()
                conn.execute(text("INSERT INTO _map VALUES (:v, :c)"),
                             [{"v": a, "c": b} for a, b in zip(m["variante"], m["canonico"])])
            conn.execute(text("UPDATE _v SET novo = COALESCE((SELECT canonico FROM _map WHERE variante = _v.norm), _v.norm)"))
            conn.execute(text("UPDATE _v SET fusao = (SELECT count(*) FROM _v v2 WHERE v2.novo = _v.novo) > 1"))

            pd.read_sql(text("SELECT norm AS variante, sum(n)::bigint AS n FROM _v GROUP BY 1 ORDER BY 2 DESC"),
                        conn).to_csv(DIR_SAIDA / f"variantes_{c}.csv", index=False)

            conn.execute(text("""
                INSERT INTO prov.transformacao_valor (id_atividade, campo, valor_original, valor_novo, regra, n_celulas, fusao)
                SELECT :ida, :c, orig, novo, 'upper_trim_unaccent+mapa', n, fusao FROM _v WHERE novo <> orig"""),
                {"ida": ida, "c": c})
            # fusão = perda de informação -> registro por linha
            conn.execute(text(f"""
                INSERT INTO prov.modificacao (rid, campo, operacao, valor_original, valor_novo, regra, id_atividade)
                SELECT t.rid, :c, 'PADRONIZACAO', t."{c}", v.novo, 'padronizacao_com_fusao', :ida
                FROM clean.datatran t JOIN _v v ON v.orig = t."{c}" WHERE v.fusao AND v.novo <> v.orig"""),
                {"ida": ida, "c": c})
            i = len(usados)
            conn.execute(text(f"CREATE TEMP TABLE _vm{i} AS SELECT orig, novo FROM _v WHERE novo <> orig"))
            usados.append(c)
            r = conn.execute(text("SELECT count(*), count(DISTINCT novo), "
                                  "coalesce(sum(n) FILTER (WHERE novo <> orig), 0), "
                                  "coalesce(sum(n) FILTER (WHERE fusao AND novo <> orig), 0) FROM _v")).one()
            resumo.append((c, int(r[0]), int(r[1]), int(r[2]), int(r[3]), "mapa" if arq.exists() else "sem mapa"))
            print(f"[{time.time() - t0:6.0f}s] {c}: {r[0]} -> {r[1]} valores distintos; "
                  f"{int(r[2])} células a alterar ({int(r[3])} em fusão)", flush=True)

        # UMA única atualização da tabela (evita reescrevê-la 18 vezes)
        sel = ", ".join(f"m{i}.novo AS n{i}" for i in range(len(usados)))
        joins = " ".join(f'LEFT JOIN _vm{i} m{i} ON m{i}.orig = t2."{c}"' for i, c in enumerate(usados))
        cond = " OR ".join(f"m{i}.novo IS NOT NULL" for i in range(len(usados)))
        sets = ", ".join(f'"{c}" = COALESCE(x.n{i}, t."{c}")' for i, c in enumerate(usados))
        print(f"[{time.time() - t0:6.0f}s] atualizando clean.datatran (uma passada)...", flush=True)
        n = conn.execute(text(f"UPDATE clean.datatran t SET {sets} FROM "
                              f"(SELECT t2.rid, {sel} FROM clean.datatran t2 {joins} WHERE {cond}) x "
                              f"WHERE t.rid = x.rid")).rowcount
        fechar_atividade(conn, ida, n)
        print(f"[{time.time() - t0:6.0f}s] linhas atualizadas: {n}", flush=True)
        print(f"\n{'campo':26} {'distintos_antes':>15} {'distintos_apos':>14} {'celulas_alt':>12} {'em_fusao':>10}")
        for c, a, b, x, f, s in resumo:
            print(f"{c:26} {a:>15} {b:>14} {x:>12} {f:>10}  {s}")


if __name__ == "__main__":
    main()
