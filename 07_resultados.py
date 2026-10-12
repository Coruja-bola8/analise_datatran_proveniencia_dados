"""Gera TODOS os números do Capítulo 4 a partir do banco e salva saida/resultados_cap4.md.
Rode depois das etapas 03-06. A reversibilidade é testada à parte (08_reversibilidade.py)."""
import numbers
import pandas as pd
from sqlalchemy import create_engine, text
from config import *
from params import *
from prov import colunas_publicadas
from config import DB_URL, DIR_SAIDA, DIR_MAPAS, CAMPOS_PADRONIZAR, CAMPOS_CONJUNTO


pd.set_option("display.width", 250, "display.max_rows", 500, "display.max_columns", 50)
saida = []


def md(df):
    d = df.copy()
    d.columns = [str(c) for c in d.columns]
    lin = ["| " + " | ".join(d.columns) + " |", "|" + "|".join("---" for _ in d.columns) + "|"]
    for _, r in d.iterrows():
        lin.append("| " + " | ".join("" if pd.isna(x) else (f"{x:,.0f}".replace(",", ".") if isinstance(x, numbers.Real) and float(x).is_integer() else str(x)) for x in r) + " |")
    return "\n".join(lin)


def secao(titulo, df, nota=None):
    print(f"\n=== {titulo} ===")
    print(df.to_string(index=False))
    saida.append(f"## {titulo}\n")
    if nota:
        saida.append(nota + "\n")
    saida.append(md(df) + "\n")


def main():
    DIR_SAIDA.mkdir(exist_ok=True)
    eng = create_engine(DB_URL)
    with eng.connect() as conn:
        q = lambda s, **p: pd.read_sql(text(s), conn, params=p)
        cols = colunas_publicadas(conn)

        secao("1. Camada de origem (arquivos)", q("""
            SELECT ano, nome_arquivo, encoding, n_linhas, n_colunas, left(sha256, 12) AS sha256_12
            FROM prov.arquivo_origem ORDER BY ano"""), f"Campos publicados distintos: {len(cols)}")

        secao("2. Volume por ano", q("""
            SELECT a.ano, count(*) AS linhas, count(DISTINCT r.id) AS acidentes
            FROM raw.datatran_primario r JOIN prov.arquivo_origem a USING (id_arquivo) GROUP BY a.ano ORDER BY 1"""))

        secao("3. Duplicatas", q("""
            SELECT 'linhas na tabela primária' AS item, count(*) AS n FROM raw.datatran_primario
            UNION ALL SELECT 'descartes (linha idêntica)', count(*) FROM prov.modificacao WHERE operacao = 'DESCARTE'
            UNION ALL SELECT 'linhas em clean.datatran', count(*) FROM clean.datatran
            UNION ALL SELECT 'acidentes (ids distintos)', count(DISTINCT id) FROM raw.datatran_primario"""))

        secao("3b. Chave do TCC original (data, horário, km, BR, UF) aplicada aos dados reais", q("""
            SELECT count(*) AS grupos_pela_chave,
                   count(*) FILTER (WHERE n_ids > 1) AS grupos_com_mais_de_um_acidente,
                   sum(n_linhas) - count(*) AS linhas_que_a_chave_marcaria_como_duplicata
            FROM (SELECT count(*) AS n_linhas, count(DISTINCT id) AS n_ids FROM raw.datatran_primario
                  GROUP BY data_inversa, horario, km, br, uf) t"""),
            "Mostra por que a chave original não identifica duplicatas nestes dados (várias pessoas por acidente).")

        secao("4a. Textos de ausência convertidos em NULL (por campo)", q("""
            SELECT campo, valor_original AS texto, count(*) AS celulas
            FROM prov.modificacao WHERE regra = 'token_ausencia_para_nulo'
            GROUP BY 1, 2 ORDER BY 3 DESC"""))

        secao("4b. NULL -> 'Ignorado' (por campo)", q("""
            SELECT campo, count(*) AS celulas FROM prov.modificacao WHERE regra = 'categoria_ignorado'
            GROUP BY 1 ORDER BY 2 DESC"""))

        secao("4c. Coordenadas por origem (linhas e acidentes)", q("""
            SELECT l.coord_status, l.linhas, a.acidentes FROM
              (SELECT coord_status, count(*) AS linhas FROM clean.datatran GROUP BY 1) l
              LEFT JOIN (SELECT coord_status, count(*) AS acidentes FROM clean.acidente GROUP BY 1) a
              USING (coord_status)"""),
            "Imputações de coordenada (latitude/longitude) no log: " +
            str(conn.execute(text("SELECT count(*) FROM prov.modificacao WHERE operacao='IMPUTACAO' "
                                  "AND campo IN ('latitude','longitude')")).scalar()))

        d5 = pd.DataFrame(
            [(c, conn.execute(text(f'SELECT count(DISTINCT "{c}") FROM raw.datatran_primario')).scalar(),
              conn.execute(text(f'SELECT count(DISTINCT "{c}") FROM clean.datatran')).scalar())
             for c in [x for x in CAMPOS_PADRONIZAR if x in cols]],
            columns=["campo", "distintos_brutos", "distintos_apos"])
        tv = q("""SELECT campo, count(*)::bigint AS pares_alterados, sum(n_celulas)::bigint AS celulas_alteradas,
                         coalesce(sum(n_celulas) FILTER (WHERE fusao), 0)::bigint AS celulas_em_fusao
                  FROM prov.transformacao_valor GROUP BY 1""")
        secao("5. Padronização: valores distintos antes e depois", d5.merge(tv, on="campo", how="left").fillna(0),
              "Registro por valor em prov.transformacao_valor; por linha apenas nas fusões.")

        secao("6a. Validação geoespacial (linhas)", q("""
            SELECT coalesce(validacao_geo, '(sem coordenada utilizável)') AS resultado, count(*) AS linhas
            FROM clean.geo_linha GROUP BY 1 ORDER BY 2 DESC"""))
        secao("6b. Validação geoespacial (acidentes)", q("""
            SELECT coalesce(validacao_geo, '(sem coordenada utilizável)') AS resultado, count(*) AS acidentes
            FROM clean.acidente GROUP BY 1 ORDER BY 2 DESC"""))
        secao("6c. Acidentes com coordenadas divergentes entre as linhas do mesmo id", q(
            "SELECT count(*) FILTER (WHERE coord_conflito) AS ids_com_conflito, count(*) AS acidentes FROM clean.acidente"))

        secao("7. Precisão decimal da latitude por ano (acidentes)", q("""
            SELECT date_part('year', data_hora)::int AS ano,
              count(*) FILTER (WHERE casas_decimais_lat = 0) AS sem_decimais,
              count(*) FILTER (WHERE casas_decimais_lat BETWEEN 1 AND 3) AS dec_1a3,
              count(*) FILTER (WHERE casas_decimais_lat BETWEEN 4 AND 5) AS dec_4a5,
              count(*) FILTER (WHERE casas_decimais_lat BETWEEN 6 AND 7) AS dec_6a7,
              count(*) FILTER (WHERE casas_decimais_lat >= 8) AS dec_8mais, count(*) AS acidentes
            FROM clean.acidente GROUP BY 1 ORDER BY 1"""))

        secao("8. Inventário do registro de modificações", q("""
            SELECT m.operacao, m.regra, a.etapa, count(*) AS modificacoes, count(DISTINCT m.rid) AS linhas_afetadas
            FROM prov.modificacao m JOIN prov.atividade a USING (id_atividade)
            GROUP BY 1, 2, 3 ORDER BY 3, 1, 2"""))

        secao("8b. Registro por valor da padronização", q("""
            SELECT regra, count(*) AS pares_valor, sum(n_celulas)::bigint AS celulas,
                   count(*) FILTER (WHERE fusao) AS pares_em_fusao FROM prov.transformacao_valor GROUP BY 1"""))

        secao("9. Distinguibilidade: origem da coordenada obtida SÓ pelo log vs coord_status", q("""
            SELECT v.origem_coord, count(*) AS linhas,
                   count(*) FILTER (WHERE v.origem_coord <> c.coord_status) AS divergentes_de_coord_status
            FROM clean.v_coord_origem v JOIN clean.datatran c USING (rid) GROUP BY 1"""))

        secao("10. Atividades registradas (modelo PROV)", q("""
            SELECT a.id_atividade, a.etapa, g.script, g.versao, left(g.sha256_codigo, 10) AS hash_script,
                   a.inicio, a.fim, a.n_linhas_afetadas
            FROM prov.atividade a JOIN prov.agente g USING (id_agente) ORDER BY 1"""))

    (DIR_SAIDA / "resultados_cap4.md").write_text("# Resultados para o Capítulo 4\n\n" + "\n".join(saida), encoding="utf-8")
    print("\nSalvo em saida/resultados_cap4.md")


if __name__ == "__main__":
    main()
