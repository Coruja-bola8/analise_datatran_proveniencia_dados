"""Teste empírico de reversibilidade (Seção 3.3 / 4.4). Reconstrói os campos publicados a partir de
clean.datatran + registros de proveniência e compara, linha a linha (md5), com raw.datatran_primario.
Desfaz as etapas na ordem inversa:
  E4: (a) pares por valor NÃO fundidos -> valor_original; (b) linhas em fusão -> valor_original do log por linha
  E3: primeira modificação de (rid, campo) guarda o valor que veio da tabela primária."""
from sqlalchemy import create_engine, text
from config import *
from prov import colunas_publicadas

E3 = "('token_ausencia_para_nulo', 'categoria_ignorado', 'mediana_por_chave')"


def main():
    eng = create_engine(DB_URL)
    with eng.begin() as conn:
        cols = colunas_publicadas(conn)
        sel = ", ".join(f'"{c}"' for c in cols) + ", latitude_num, longitude_num"
        conn.execute(text(f"CREATE TEMP TABLE _rev AS SELECT rid, {sel} FROM clean.datatran"))
        conn.execute(text("CREATE INDEX ON _rev (rid)"))

        campos_e4 = conn.execute(text("SELECT DISTINCT campo FROM prov.transformacao_valor")).scalars().all()
        for c in campos_e4:
            conn.execute(text(f"""UPDATE _rev SET "{c}" = vt.valor_original
                FROM prov.transformacao_valor vt
                WHERE vt.campo = :c AND NOT vt.fusao AND _rev."{c}" = vt.valor_novo"""), {"c": c})
            conn.execute(text(f"""UPDATE _rev SET "{c}" = m.valor_original
                FROM (SELECT DISTINCT ON (rid) rid, valor_original FROM prov.modificacao
                      WHERE campo = :c AND regra = 'padronizacao_com_fusao' ORDER BY rid, id_mod) m
                WHERE _rev.rid = m.rid"""), {"c": c})
            print("E4 desfeita:", c, flush=True)

        campos_e3 = conn.execute(text(f"SELECT DISTINCT campo FROM prov.modificacao WHERE regra IN {E3}")).scalars().all()
        for c in campos_e3:
            if c in ("latitude", "longitude"):
                alvo = f"{c}_num"
                valor = ("CASE WHEN m.valor_original ~ '^-?[0-9]+([.,][0-9]+)?$' "
                         "THEN replace(m.valor_original, ',', '.')::double precision END")
            else:
                alvo, valor = f'"{c}"', "m.valor_original"
            conn.execute(text(f"""UPDATE _rev SET {alvo} = {valor}
                FROM (SELECT DISTINCT ON (rid) rid, valor_original FROM prov.modificacao
                      WHERE campo = :c AND regra IN {E3} ORDER BY rid, id_mod) m
                WHERE _rev.rid = m.rid"""), {"c": c})
            print("E3 desfeita:", c, flush=True)

        h = f"md5(ROW({sel})::text)"
        n_rev = conn.execute(text("SELECT count(*) FROM _rev")).scalar()
        dif = conn.execute(text(f"""
            SELECT count(*) FROM (
              SELECT rid, {h} AS h FROM raw.datatran_primario WHERE rid IN (SELECT rid FROM clean.datatran)
              EXCEPT SELECT rid, {h} FROM _rev) x""")).scalar()
        orf = conn.execute(text("""
            SELECT count(*) FROM prov.modificacao m WHERE operacao = 'DESCARTE'
              AND (NOT EXISTS (SELECT 1 FROM raw.datatran_primario r WHERE r.rid = m.rid)
                OR NOT EXISTS (SELECT 1 FROM clean.datatran c WHERE c.rid = m.rid_relacionado))""")).scalar()
        print(f"\nLinhas reconstruídas: {n_rev}")
        print(f"Linhas que NÃO voltam idênticas à tabela primária: {dif}")
        print(f"Descartes sem registro bruto ou sem registro mantido: {orf}")
        print("RESULTADO:", "REVERSÍVEL (0 divergências)" if dif == 0 and orf == 0 else "HÁ DIVERGÊNCIAS")


if __name__ == "__main__":
    main()
