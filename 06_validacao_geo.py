"""Etapa 5 (v2): validação geoespacial, feita sobre PONTOS DISTINTOS (uf, br, lat, lon) e devolvida às linhas.
Prioridade dos testes: FORA_BRASIL > UF_INCOMPATIVEL > DIST_RODOVIA. Linhas sem BR (NULL) ou BR sem geometria
no DNIT ficam 'OK_SEM_GEOM_RODOVIA' (distância não verificável). Ao final cria clean.acidente (1 linha por id)."""
import json
from pathlib import Path
import geopandas as gpd
import pandas as pd
from sqlalchemy import create_engine, text
from config import *
from params import *
from prov import abrir_atividade, fechar_atividade

ETAPA = "E5_validacao_geo"
CHAVE_PONTO = ("md5(coalesce(upper(trim({uf})),'') || '|' || coalesce({br}::text,'') || '|' || "
               "{lat}::text || '|' || {lon}::text)")


def carregar_auxiliares(eng):
    uf = gpd.read_file(UF_ARQUIVO).to_crs(4674)[[UF_COL_SIGLA, "geometry"]]
    uf = uf.rename(columns={UF_COL_SIGLA: "sigla"}).rename_geometry("geom")
    uf["sigla"] = uf["sigla"].astype(str).str.upper().str.strip()
    uf.to_postgis("uf", eng, schema="aux", if_exists="replace", index=False)

    rod = gpd.read_file(RODOVIAS_ARQUIVO).to_crs(5880)[[RODOVIAS_COL_BR, "geometry"]]
    rod["br"] = pd.to_numeric(rod[RODOVIAS_COL_BR], errors="coerce")
    rod = rod.dropna(subset=["br"]).astype({"br": int})[["br", "geometry"]]
    rod = rod.explode(index_parts=False).rename_geometry("geom")
    rod.to_postgis("rodovia_seg", eng, schema="aux", if_exists="replace", index=False)
    with eng.begin() as conn:
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_aux_uf ON aux.uf USING gist (geom)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_aux_rod ON aux.rodovia_seg USING gist (geom)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_aux_rod_br ON aux.rodovia_seg (br)"))
    print(f"Auxiliares: {len(uf)} UF, {len(rod)} segmentos de rodovia ({rod['br'].nunique()} BRs)")


def main():
    eng = create_engine(DB_URL)
    carregar_auxiliares(eng)
    with eng.begin() as conn:
        conn.execute(text("""DELETE FROM prov.modificacao WHERE id_atividade IN
                             (SELECT id_atividade FROM prov.atividade WHERE etapa = :e)"""), {"e": ETAPA})
        conn.execute(text("DELETE FROM prov.atividade WHERE etapa = :e"), {"e": ETAPA})
        conn.execute(text("DROP TABLE IF EXISTS clean.acidente"))
        conn.execute(text("DROP TABLE IF EXISTS clean.geo_linha"))

        params = {"lat_lim": LAT_LIM, "lon_lim": LON_LIM, "tolerancia_m": TOLERANCIA_M, "crs_pontos": 4674,
                  "crs_distancia": 5880, "prioridade": "FORA_BRASIL > UF > DISTANCIA",
                  "unidade_de_calculo": "pontos distintos (uf, br, lat, lon)"}
        p = json.dumps(params)
        ida = abrir_atividade(conn, ETAPA, __file__, params, entrada="clean.datatran", saida="clean.datatran")

        k_pts = CHAVE_PONTO.format(uf="uf", br="br", lat="lat", lon="lon")
        conn.execute(text(f"""
            CREATE TEMP TABLE _pts AS
            SELECT DISTINCT upper(trim(uf)) AS uf, aux.br_int(br) AS br,
                   latitude_num AS lat, longitude_num AS lon
            FROM clean.datatran WHERE coord_status IN ('OBSERVADA', 'DERIVADA')"""))
        conn.execute(text(f"ALTER TABLE _pts ADD COLUMN k text, ADD COLUMN g4674 geometry(Point, 4674), "
                          f"ADD COLUMN g5880 geometry(Point, 5880), ADD COLUMN motivo text"))
        conn.execute(text(f"UPDATE _pts SET k = {k_pts}"))
        conn.execute(text("""
            UPDATE _pts SET g4674 = ST_SetSRID(ST_MakePoint(lon, lat), 4674),
                g5880 = ST_Transform(ST_SetSRID(ST_MakePoint(lon, lat), 4674), 5880)
            WHERE lat BETWEEN -90 AND 90 AND lon BETWEEN -180 AND 180"""))
        conn.execute(text("CREATE INDEX ON _pts USING gist (g5880)"))
        conn.execute(text("""
            UPDATE _pts SET motivo = CASE
              WHEN g4674 IS NULL OR NOT (lat BETWEEN :la0 AND :la1 AND lon BETWEEN :lo0 AND :lo1)
                THEN 'FORA_BRASIL'
              WHEN NOT EXISTS (SELECT 1 FROM aux.uf u WHERE u.sigla = _pts.uf AND ST_Intersects(u.geom, _pts.g4674))
                THEN 'UF_INCOMPATIVEL'
              WHEN NOT EXISTS (SELECT 1 FROM aux.rodovia_seg r WHERE r.br = _pts.br)
                THEN 'OK_SEM_GEOM_RODOVIA'
              WHEN NOT EXISTS (SELECT 1 FROM aux.rodovia_seg r WHERE r.br = _pts.br
                               AND ST_DWithin(r.geom, _pts.g5880, :tol))
                THEN 'DIST_RODOVIA'
              ELSE 'OK' END"""),
            {"la0": LAT_LIM[0], "la1": LAT_LIM[1], "lo0": LON_LIM[0], "lo1": LON_LIM[1], "tol": TOLERANCIA_M})

        # Resultado em tabela ESTREITA (evita reescrever clean.datatran, que tem 37 colunas de texto)
        k_row = CHAVE_PONTO.format(uf="c.uf", br="aux.br_int(c.br)", lat="c.latitude_num", lon="c.longitude_num")
        conn.execute(text(f"""
            CREATE TABLE clean.geo_linha AS
            SELECT c.rid, p.motivo AS validacao_geo,
                   length(split_part(replace(c.latitude, ',', '.'), '.', 2)) AS casas_decimais_lat
            FROM clean.datatran c
            LEFT JOIN _pts p ON c.coord_status IN ('OBSERVADA', 'DERIVADA') AND {k_row} = p.k"""))
        conn.execute(text("ALTER TABLE clean.geo_linha ADD PRIMARY KEY (rid)"))
        conn.execute(text("""
            INSERT INTO prov.modificacao (rid, campo, operacao, valor_original, valor_novo, regra, parametros, id_atividade)
            SELECT rid, 'validacao_geo', 'MARCACAO', NULL, validacao_geo, 'validacao_geoespacial',
                   CAST(:p AS jsonb), :ida
            FROM clean.geo_linha WHERE validacao_geo IN ('FORA_BRASIL', 'UF_INCOMPATIVEL', 'DIST_RODOVIA')"""),
            {"p": p, "ida": ida})
        conn.execute(text("ALTER TABLE clean.datatran DROP COLUMN IF EXISTS validacao_geo"))
        conn.execute(text("ALTER TABLE clean.datatran DROP COLUMN IF EXISTS casas_decimais_lat"))
        fechar_atividade(conn, ida)

        # tabela de acidentes (1 linha por id); NÃO descarta linhas de clean.datatran
        conn.execute(text("DROP TABLE IF EXISTS clean.acidente"))
        conn.execute(text("""
            CREATE TABLE clean.acidente AS
            WITH g AS (SELECT id, min(rid) AS rid_ref, count(*) AS n_linhas,
                              count(DISTINCT latitude_num::text || '|' || longitude_num::text) > 1 AS coord_conflito
                       FROM clean.datatran GROUP BY id)
            SELECT g.id, g.rid_ref, g.n_linhas, g.coord_conflito, c.data_hora, c.uf, c.br, c.km, c.municipio,
                   c.classificacao_acidente, c.latitude_num, c.longitude_num, c.coord_status,
                   gl.validacao_geo, gl.casas_decimais_lat
            FROM g JOIN clean.datatran c ON c.rid = g.rid_ref
            LEFT JOIN clean.geo_linha gl ON gl.rid = c.rid"""))
        conn.execute(text("ALTER TABLE clean.acidente ADD PRIMARY KEY (id)"))
        conn.execute(text(Path("sql/10_views_clean.sql").read_text(encoding="utf-8")))

        print("Linhas por validacao_geo:")
        for m, n in conn.execute(text("SELECT validacao_geo, count(*) FROM clean.geo_linha GROUP BY 1 ORDER BY 2 DESC")):
            print(f"  {str(m):22} {n}")
        print("Acidentes por validacao_geo (clean.acidente):")
        for m, n in conn.execute(text("SELECT validacao_geo, count(*) FROM clean.acidente GROUP BY 1 ORDER BY 2 DESC")):
            print(f"  {str(m):22} {n}")


if __name__ == "__main__":
    main()