"""Compara o que o pipeline produziu com os números do TCC e executa o teste de reversibilidade
(a validação que o TCC diz ainda não ter feito, Seção 4.4)."""
import pandas as pd
from sqlalchemy import create_engine, text

from config import *
from prov import colunas_publicadas

# (métrica, valor no TCC, consulta SQL que devolve um número)
Q = lambda s: s
METRICAS = [
    ("Campos publicados (Seção 3.2)", 31, None),
    ("Registros brutos 2017-2024", 1512340, "SELECT count(*) FROM raw.datatran_primario"),
    ("Duplicatas descartadas", 47823, "SELECT count(*) FROM prov.modificacao WHERE operacao='DESCARTE'"),
    ("Registros únicos", 1464517, "SELECT count(*) FROM clean.datatran"),
    ("% latitude ausente (base bruta)", 18.4, "SELECT round(100.0*count(*) FILTER (WHERE latitude_num IS NULL)/count(*),1) FROM raw.datatran_primario"),
    ("% longitude ausente (base bruta)", 18.6, "SELECT round(100.0*count(*) FILTER (WHERE longitude_num IS NULL)/count(*),1) FROM raw.datatran_primario"),
    ("% lat ausente 2017", 24.3, "SELECT round(100.0*count(*) FILTER (WHERE r.latitude_num IS NULL)/count(*),1) FROM raw.datatran_primario r JOIN prov.arquivo_origem a USING (id_arquivo) WHERE a.ano=2017"),
    ("% lat ausente 2024", 11.7, "SELECT round(100.0*count(*) FILTER (WHERE r.latitude_num IS NULL)/count(*),1) FROM raw.datatran_primario r JOIN prov.arquivo_origem a USING (id_arquivo) WHERE a.ano=2024"),
    ("% condicao_metereologica ausente", 9.2, "SELECT round(100.0*count(*) FILTER (WHERE condicao_metereologica IS NULL)/count(*),1) FROM raw.datatran_primario"),
    ("% tracado_via ausente", 6.8, "SELECT round(100.0*count(*) FILTER (WHERE tracado_via IS NULL)/count(*),1) FROM raw.datatran_primario"),
    ("Sem coordenadas após deduplicação", 264023, "SELECT count(*) FROM clean.datatran WHERE coord_status IN ('DERIVADA','IRRECUPERAVEL')"),
    ("Registros recuperados (imputados)", 31847, "SELECT count(DISTINCT rid) FROM prov.modificacao WHERE operacao='IMPUTACAO' AND campo IN ('latitude','longitude')"),
    ("Irrecuperáveis", 232176, "SELECT count(*) FROM clean.datatran WHERE coord_status='IRRECUPERAVEL'"),
    ("Com coordenadas disponíveis", 1232341, "SELECT count(*) FROM clean.datatran WHERE coord_status IN ('OBSERVADA','DERIVADA')"),
    ("Reprovados na validação", 14328, "SELECT count(*) FROM clean.datatran WHERE validacao_geo IN ('FORA_BRASIL','UF_INCOMPATIVEL','DIST_RODOVIA')"),
    ("  fora do Brasil", 3241, "SELECT count(*) FROM clean.datatran WHERE validacao_geo='FORA_BRASIL'"),
    ("  UF incompatível", 6872, "SELECT count(*) FROM clean.datatran WHERE validacao_geo='UF_INCOMPATIVEL'"),
    ("  > 2 km da rodovia", 4215, "SELECT count(*) FROM clean.datatran WHERE validacao_geo='DIST_RODOVIA'"),
    ("Válidos e verificados", 1218013, "SELECT count(*) FROM clean.datatran WHERE validacao_geo LIKE 'OK%'"),
    ("% derivadas entre as com coordenadas", 2.6, "SELECT round(100.0*count(*) FILTER (WHERE coord_status='DERIVADA')/count(*),1) FROM clean.datatran WHERE coord_status IN ('OBSERVADA','DERIVADA')"),
    ("Variantes brutas de causa_acidente", 847, 'SELECT count(DISTINCT causa_acidente) FROM raw.datatran_primario'),
    ("Categorias de causa_acidente após padronização", 35, 'SELECT count(DISTINCT causa_acidente) FROM clean.datatran'),
    ("Variantes brutas de tipo_acidente", 312, 'SELECT count(DISTINCT tipo_acidente) FROM raw.datatran_primario'),
    ("Categorias de tipo_acidente após padronização", 18, 'SELECT count(DISTINCT tipo_acidente) FROM clean.datatran'),
]


def reversibilidade(conn, cols):
    conn.execute(text("DROP TABLE IF EXISTS _rev"))
    sel = ", ".join(f'"{c}"' for c in cols)
    conn.execute(text(f"CREATE TEMP TABLE _rev AS SELECT rid, {sel}, latitude_num, longitude_num FROM clean.datatran"))
    campos = conn.execute(text("SELECT DISTINCT campo FROM prov.modificacao "
                               "WHERE operacao IN ('IMPUTACAO','PADRONIZACAO')")).scalars().all()
    for campo in campos:
        if campo in ("latitude", "longitude"):
            alvo = f"{campo}_num"
            valor = ("CASE WHEN m.valor_original ~ '^-?[0-9]+([.,][0-9]+)?$' "
                     "THEN replace(m.valor_original, ',', '.')::double precision END")
        else:
            alvo, valor = f'"{campo}"', "m.valor_original"
        # a PRIMEIRA modificação de (rid, campo) guarda o valor que veio da tabela primária
        conn.execute(text(f"""
            UPDATE _rev SET {alvo} = {valor}
            FROM (SELECT DISTINCT ON (rid) rid, valor_original FROM prov.modificacao
                  WHERE campo = :c AND operacao IN ('IMPUTACAO','PADRONIZACAO')
                  ORDER BY rid, id_mod) m
            WHERE _rev.rid = m.rid"""), {"c": campo})
    dif = conn.execute(text(f"""
        SELECT count(*) FROM (
          SELECT rid, {sel}, latitude_num, longitude_num FROM raw.datatran_primario
          WHERE rid IN (SELECT rid FROM clean.datatran)
          EXCEPT SELECT * FROM _rev) x""")).scalar()
    orfaos = conn.execute(text("""
        SELECT count(*) FROM prov.modificacao m
        WHERE operacao='DESCARTE'
          AND (NOT EXISTS (SELECT 1 FROM raw.datatran_primario r WHERE r.rid = m.rid)
            OR NOT EXISTS (SELECT 1 FROM clean.datatran c WHERE c.rid = m.rid_relacionado))""")).scalar()
    return dif, orfaos


def main():
    eng = create_engine(DB_URL)
    linhas = []
    with eng.connect() as conn:
        cols = colunas_publicadas(conn)
        for nome, esperado, sql in METRICAS:
            try:
                obtido = len(cols) if sql is None else conn.execute(text(sql)).scalar()
                obtido = float(obtido) if obtido is not None else None
            except Exception as e:
                conn.rollback()
                obtido = None
                print(f"[erro] {nome}: {str(e).splitlines()[0]}")
            linhas.append((nome, esperado, obtido, None if obtido is None else round(obtido - esperado, 2)))
        df = pd.DataFrame(linhas, columns=["metrica", "tcc", "obtido", "diferenca"])
        pd.set_option("display.width", 200, "display.max_rows", 200, "display.float_format", "{:,.2f}".format)
        print(df.to_string(index=False))
        df.to_csv(DIR_SAIDA / "comparacao_tcc.csv", index=False)

        dif, orf = reversibilidade(conn, cols)
        print(f"\nReversibilidade: registros que NÃO voltam idênticos à tabela primária = {dif}")
        print(f"Descartes sem registro bruto ou sem registro mantido = {orf}")

        r = conn.execute(text("""
            SELECT count(*) FROM clean.v_coord_origem v JOIN clean.datatran c USING (rid)
            WHERE v.origem_coord <> c.coord_status""")).scalar()
        print(f"Distinguibilidade: divergências entre a view do log e coord_status = {r}")


if __name__ == "__main__":
    main()
