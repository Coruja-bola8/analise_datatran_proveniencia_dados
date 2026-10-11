"""Etapa 3 (v2): ausências.
 (a) textos de ausência ('NA', 'N/A') -> NULL, com o texto original no log;
 (b) coordenadas: imputação pela mediana de (rodovia, km) SOMENTE se houver coordenada ausente
     (nos dados 2017-2025 não há; o script registra zero);
 (c) NULL em campos categóricos do acidente -> 'Ignorado'."""
import json
from sqlalchemy import create_engine, text
from config import *
from params import *
from prov import abrir_atividade, fechar_atividade, colunas_publicadas, exigir_nao_executada

ETAPA = "E3_ausentes"
INS = ("INSERT INTO prov.modificacao (rid, campo, operacao, valor_original, valor_novo, regra, parametros, id_atividade) ")


def main():
    eng = create_engine(DB_URL)
    with eng.begin() as conn:
        exigir_nao_executada(conn, ETAPA)
        cols = colunas_publicadas(conn)
        params = {"tokens_ausencia": TOKENS_AUSENCIA, "chave_imputacao": CHAVE_IMPUTACAO,
                  "categoricos_ignorado": CAMPOS_CATEGORICOS_IGNORADO}
        p = json.dumps(params)
        ida = abrir_atividade(conn, ETAPA, __file__, params, entrada="clean.datatran", saida="clean.datatran")

        # (a) tokens -> NULL
        toks = ", ".join(f"'{t.upper()}'" for t in TOKENS_AUSENCIA)
        n_tok = {}
        for c in cols:
            cond = f'upper(trim("{c}")) IN ({toks})'
            conn.execute(text(INS + f"""SELECT rid, :c, 'PADRONIZACAO', "{c}", NULL, 'token_ausencia_para_nulo',
                                       CAST(:p AS jsonb), :ida FROM clean.datatran WHERE {cond}"""),
                         {"c": c, "p": p, "ida": ida})
            n = conn.execute(text(f'UPDATE clean.datatran SET "{c}" = NULL WHERE {cond}')).rowcount
            if n:
                n_tok[c] = n
        print("Tokens de ausência convertidos em NULL por campo:", n_tok)

        # (b) coordenadas
        conn.execute(text("UPDATE clean.datatran SET coord_status = 'OBSERVADA' "
                          "WHERE latitude_num IS NOT NULL AND longitude_num IS NOT NULL"))
        n_sem = conn.execute(text("SELECT count(*) FROM clean.datatran "
                                  "WHERE latitude_num IS NULL OR longitude_num IS NULL")).scalar()
        print("Linhas sem latitude ou longitude:", n_sem)
        if n_sem:
            g = ", ".join(f'"{c}"' for c in CHAVE_IMPUTACAO)
            nn = " AND ".join(f'"{c}" IS NOT NULL' for c in CHAVE_IMPUTACAO)
            jn = " AND ".join(f'c."{c}" = m."{c}"' for c in CHAVE_IMPUTACAO)
            conn.execute(text(f"""
                CREATE TEMP TABLE _med ON COMMIT DROP AS
                SELECT {g}, percentile_cont(0.5) WITHIN GROUP (ORDER BY latitude_num) AS lat_med,
                       percentile_cont(0.5) WITHIN GROUP (ORDER BY longitude_num) AS lon_med
                FROM clean.datatran
                WHERE latitude_num IS NOT NULL AND longitude_num IS NOT NULL AND {nn} GROUP BY {g}"""))
            conn.execute(text(f"""
                CREATE TEMP TABLE _imp ON COMMIT DROP AS
                SELECT c.rid, c.latitude AS lat_txt, c.longitude AS lon_txt, c.latitude_num AS lat_old,
                       c.longitude_num AS lon_old, m.lat_med, m.lon_med
                FROM clean.datatran c JOIN _med m ON {jn}
                WHERE c.latitude_num IS NULL OR c.longitude_num IS NULL"""))
            for campo, txt, old, med in (("latitude", "lat_txt", "lat_old", "lat_med"),
                                         ("longitude", "lon_txt", "lon_old", "lon_med")):
                conn.execute(text(INS + f"""SELECT rid, '{campo}', 'IMPUTACAO', {txt}, {med}::text,
                    'mediana_por_chave', CAST(:p AS jsonb), :ida FROM _imp WHERE {old} IS NULL"""),
                             {"p": p, "ida": ida})
            conn.execute(text("""UPDATE clean.datatran c SET latitude_num = COALESCE(c.latitude_num, i.lat_med),
                longitude_num = COALESCE(c.longitude_num, i.lon_med), coord_status = 'DERIVADA'
                FROM _imp i WHERE c.rid = i.rid"""))
            conn.execute(text(INS + """SELECT rid, 'coord_status', 'MARCACAO', NULL, 'IRRECUPERAVEL',
                'sem_correspondente_na_chave', CAST(:p AS jsonb), :ida FROM clean.datatran
                WHERE latitude_num IS NULL OR longitude_num IS NULL"""), {"p": p, "ida": ida})
            conn.execute(text("UPDATE clean.datatran SET coord_status = 'IRRECUPERAVEL' "
                              "WHERE latitude_num IS NULL OR longitude_num IS NULL"))
        else:
            print("Nenhuma coordenada ausente: imputação não aplicada (0 operações).")

        # (c) categóricos -> 'Ignorado'
        n_cat = {}
        for c in [x for x in CAMPOS_CATEGORICOS_IGNORADO if x in cols]:
            conn.execute(text(INS + f"""SELECT rid, :c, 'IMPUTACAO', NULL, 'Ignorado', 'categoria_ignorado',
                CAST(:p AS jsonb), :ida FROM clean.datatran WHERE "{c}" IS NULL"""), {"c": c, "p": p, "ida": ida})
            n = conn.execute(text(f"UPDATE clean.datatran SET \"{c}\" = 'Ignorado' WHERE \"{c}\" IS NULL")).rowcount
            if n:
                n_cat[c] = n
        print("NULL -> 'Ignorado' por campo:", n_cat)
        fechar_atividade(conn, ida)


if __name__ == "__main__":
    main()
