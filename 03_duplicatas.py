"""Etapa 2 (v2): duplicatas exatas na granularidade do arquivo (linha completa).
A chave do TCC original (data, hora, km, BR, UF) NÃO identifica duplicatas nestes dados: todas as pessoas
de um mesmo acidente compartilham esses cinco campos. Aqui a duplicata é a linha idêntica em todos os campos
publicados. Se houver, descarta (e registra); se não houver, o resultado documentado é zero descartes."""
import argparse, json, sys
from sqlalchemy import create_engine, text
from config import *
from params import *
from prov import abrir_atividade, fechar_atividade, colunas_publicadas

ETAPA = "E2_duplicatas"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refazer", action="store_true", help="recria clean.datatran e apaga o log das etapas 2-5")
    args = ap.parse_args()
    eng = create_engine(DB_URL)
    with eng.begin() as conn:
        if conn.execute(text("SELECT to_regclass('clean.datatran')")).scalar():
            if not args.refazer:
                sys.exit("clean.datatran já existe. Use --refazer.")
            conn.execute(text("DROP TABLE clean.datatran CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS clean.acidente"))
            conn.execute(text("DELETE FROM prov.modificacao"))
            conn.execute(text("DELETE FROM prov.atividade WHERE etapa <> 'E0_ingestao'"))

        cols = colunas_publicadas(conn)
        linha = "ROW(" + ", ".join(f'"{c}"' for c in cols) + ")::text"
        params = {"criterio": "linha idêntica em todos os campos publicados (md5 da linha)",
                  "mantido": "menor rid", "n_campos": len(cols)}
        ida = abrir_atividade(conn, ETAPA, __file__, params, entrada="raw.datatran_primario", saida="clean.datatran")

        conn.execute(text(f"""
            CREATE TEMP TABLE _rank ON COMMIT DROP AS
            SELECT rid, ROW_NUMBER() OVER w AS pos, FIRST_VALUE(rid) OVER w AS rid_mantido
            FROM raw.datatran_primario
            WINDOW w AS (PARTITION BY md5({linha}) ORDER BY rid)"""))
        conn.execute(text("""
            INSERT INTO prov.modificacao (rid, campo, operacao, rid_relacionado, regra, parametros, id_atividade)
            SELECT rid, NULL, 'DESCARTE', rid_mantido, 'duplicata_linha_identica', CAST(:p AS jsonb), :ida
            FROM _rank WHERE pos > 1"""), {"p": json.dumps(params), "ida": ida})
        conn.execute(text("""
            CREATE TABLE clean.datatran AS
            SELECT r.* FROM raw.datatran_primario r JOIN _rank k USING (rid) WHERE k.pos = 1"""))
        conn.execute(text("ALTER TABLE clean.datatran ADD PRIMARY KEY (rid)"))
        conn.execute(text("ALTER TABLE clean.datatran ADD COLUMN coord_status text, ADD COLUMN validacao_geo text"))

        n_raw = conn.execute(text("SELECT count(*) FROM raw.datatran_primario")).scalar()
        n_desc = conn.execute(text("SELECT count(*) FROM _rank WHERE pos > 1")).scalar()
        fechar_atividade(conn, ida, n_desc)
        print(f"Linhas na tabela primária: {n_raw}\nDuplicatas exatas descartadas: {n_desc}\n"
              f"Linhas em clean.datatran: {n_raw - n_desc}")


if __name__ == "__main__":
    main()
