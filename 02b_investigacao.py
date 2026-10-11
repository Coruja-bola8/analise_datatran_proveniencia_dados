"""Investigação complementar sobre raw.datatran_primario (somente leitura).
Responde: (A) qual granularidade reproduz os números do TCC; (B) quais textos representam ausência
(ex.: 'NA'); (C) qualidade das coordenadas por ano; (D) consistência de atributos dentro do mesmo id.
Salve em datatran_prov/ e rode: python 02b_investigacao.py  (resultados também em saida/)."""
import pandas as pd
from sqlalchemy import create_engine, text

from config import *
from prov import colunas_publicadas

pd.set_option("display.width", 250, "display.max_rows", 300, "display.max_columns", 50)
DIR_SAIDA.mkdir(exist_ok=True)
eng = create_engine(DB_URL)


def q(conn, sql, **p):
    return pd.read_sql(text(sql), conn, params=p)


def escalar(conn, sql):
    return conn.execute(text(sql)).scalar()


with eng.connect() as conn:
    cols = colunas_publicadas(conn)

    # ---------- A. Granularidade ----------
    print("\n=== A. Contagens por granularidade (TCC: 1.512.340 registros em 2017-2024) ===")
    base = "FROM raw.datatran_primario r JOIN prov.arquivo_origem a USING (id_arquivo)"
    linhas = []
    for rotulo, filtro in (("2017-2024", "a.ano <= 2024"), ("2017-2025", "a.ano <= 2025")):
        linhas.append((rotulo, "linhas do arquivo", escalar(conn, f"SELECT count(*) {base} WHERE {filtro}")))
        linhas.append((rotulo, "ids de acidente distintos",
                       escalar(conn, f"SELECT count(DISTINCT r.id) {base} WHERE {filtro}")))
        linhas.append((rotulo, "pesid distintos",
                       escalar(conn, f"SELECT count(DISTINCT r.pesid) {base} WHERE {filtro}")))
        for nome, g in (("(id, pesid)", "r.id, r.pesid"),
                        ("(id, pesid, id_veiculo)", "r.id, r.pesid, r.id_veiculo"),
                        ("(id, id_veiculo)", "r.id, r.id_veiculo")):
            linhas.append((rotulo, f"{nome} distintos",
                           escalar(conn, f"SELECT count(*) FROM (SELECT 1 {base} WHERE {filtro} GROUP BY {g}) x")))
    A = pd.DataFrame(linhas, columns=["periodo", "granularidade", "n"])
    print(A.to_string(index=False))
    A.to_csv(DIR_SAIDA / "inv_granularidade.csv", index=False)

    dup_grao = escalar(conn, """SELECT coalesce(sum(c - 1), 0) FROM (
        SELECT count(*) c FROM raw.datatran_primario
        GROUP BY id, pesid, id_veiculo, ordem_tipo_acidente, causa_acidente, tipo_acidente
        HAVING count(*) > 1) x""")
    print("\nLinhas repetidas em (id, pesid, id_veiculo, ordem_tipo_acidente, causa_acidente, tipo_acidente):", dup_grao)

    # ---------- B. Tokens de ausência ----------
    print("\n=== B. Textos que representam ausência (por campo) ===")
    tokens = "('NA','N/A','NULL','(NULL)','NAN','NONE','-','IGNORADO','NAO INFORMADO','NÃO INFORMADO','(NAO INFORMADO)','')"
    achados = []
    for c in cols:
        r = q(conn, f"""SELECT upper(trim("{c}")) AS token, count(*) AS n FROM raw.datatran_primario
                        WHERE "{c}" IS NOT NULL AND upper(trim("{c}")) IN {tokens} GROUP BY 1""")
        for _, x in r.iterrows():
            achados.append((c, x["token"], int(x["n"])))
        n_null = escalar(conn, f'SELECT count(*) FROM raw.datatran_primario WHERE "{c}" IS NULL')
        if n_null:
            achados.append((c, "<NULL de verdade>", int(n_null)))
    B = pd.DataFrame(achados, columns=["campo", "token", "n"])
    B["pct"] = (100 * B["n"] / escalar(conn, "SELECT count(*) FROM raw.datatran_primario")).round(3)
    print(B.sort_values("n", ascending=False).to_string(index=False))
    B.to_csv(DIR_SAIDA / "inv_tokens_ausencia.csv", index=False)

    print("\nValores não numéricos em br, km, latitude, longitude:")
    for c, pat in (("br", r"^[0-9]+(\.0+)?$"), ("km", r"^[0-9]+([.,][0-9]+)?$"),
                   ("latitude", r"^-?[0-9]+([.,][0-9]+)?$"), ("longitude", r"^-?[0-9]+([.,][0-9]+)?$")):
        r = q(conn, f'SELECT "{c}" AS valor, count(*) AS n FROM raw.datatran_primario '
                    f'WHERE "{c}" !~ :p GROUP BY 1 ORDER BY 2 DESC LIMIT 8', p=pat)
        print(f"  {c}:", dict(zip(r["valor"], r["n"])) if len(r) else "nenhum")

    # ---------- C. Coordenadas por ano ----------
    print("\n=== C. Coordenadas por ano (texto original, vírgula -> ponto) ===")
    C = q(conn, f"""
        SELECT a.ano, count(*) AS linhas,
          count(*) FILTER (WHERE r.latitude_num NOT BETWEEN {LAT_LIM[0]} AND {LAT_LIM[1]}
                              OR r.longitude_num NOT BETWEEN {LON_LIM[0]} AND {LON_LIM[1]}) AS fora_caixa_br,
          count(*) FILTER (WHERE r.latitude_num = 0 OR r.longitude_num = 0) AS zero,
          count(*) FILTER (WHERE r.latitude_num > 0) AS lat_positiva,
          count(*) FILTER (WHERE length(split_part(replace(r.latitude,',','.'),'.',2)) = 0) AS sem_decimais,
          count(*) FILTER (WHERE length(split_part(replace(r.latitude,',','.'),'.',2)) BETWEEN 1 AND 3) AS dec_1a3,
          count(*) FILTER (WHERE length(split_part(replace(r.latitude,',','.'),'.',2)) BETWEEN 4 AND 5) AS dec_4a5,
          count(*) FILTER (WHERE length(split_part(replace(r.latitude,',','.'),'.',2)) BETWEEN 6 AND 7) AS dec_6a7,
          count(*) FILTER (WHERE length(split_part(replace(r.latitude,',','.'),'.',2)) >= 8) AS dec_8mais
        {base} GROUP BY a.ano ORDER BY a.ano""")
    print(C.to_string(index=False))
    C.to_csv(DIR_SAIDA / "inv_coordenadas.csv", index=False)

    # ---------- D. Consistência dentro do mesmo id ----------
    print("\n=== D. Acidentes (id) com atributos divergentes entre as linhas do mesmo id ===")
    D = []
    for rotulo, expr in (("latitude/longitude", "latitude || '|' || longitude"),
                         ("uf/br/km", "uf || '|' || br || '|' || km"),
                         ("data/horario", "data_inversa || '|' || horario"),
                         ("municipio", "municipio"),
                         ("classificacao_acidente", "classificacao_acidente")):
        n = escalar(conn, f"SELECT count(*) FROM (SELECT id FROM raw.datatran_primario "
                          f"GROUP BY id HAVING count(DISTINCT {expr}) > 1) x")
        D.append((rotulo, n))
    D = pd.DataFrame(D, columns=["atributo", "ids_com_valores_divergentes"])
    print(D.to_string(index=False))
    D.to_csv(DIR_SAIDA / "inv_consistencia_id.csv", index=False)

print("\nResultados salvos em saida/inv_*.csv")
