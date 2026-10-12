"""Camada de dados primários: importa os CSV anuais para raw.datatran_primario (imutável)
e registra a origem de cada arquivo (Seção 3.2 e 3.3)."""
import datetime as dt
import io
import sys

import pandas as pd
from sqlalchemy import create_engine, text

from config import DB_URL, DIR_CSV, PADRAO_ARQUIVO, URL_POR_ANO, ANOS
from prov import abrir_atividade, fechar_atividade, entidade, sha256_arquivo

ETAPA = "E0_ingestao"
TECNICAS = ["id_arquivo", "linha_arquivo"]


def ler_csv(caminho, nrows=None):
    ultimo = None
    for enc in ("utf-8-sig", "latin-1"):
        try:
            df = pd.read_csv(caminho, sep=";", dtype=str, keep_default_na=False,
                             na_values=[""], encoding=enc, nrows=nrows)
            df.columns = [c.strip().lower() for c in df.columns]
            return df, enc
        except UnicodeDecodeError as e:
            ultimo = e
    raise ultimo


def para_float(s):
    return pd.to_numeric(s.str.strip().str.replace(",", ".", regex=False), errors="coerce")


def data_hora(df):
    if "data_inversa" not in df or "horario" not in df:
        return pd.Series(pd.NaT, index=df.index)
    s = df["data_inversa"].str.strip() + " " + df["horario"].fillna("00:00:00").str.strip()
    iso = s.str.match(r"^\d{4}-\d{2}-\d{2}", na=False)
    dh = pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns]")
    if iso.any():
        dh[iso] = pd.to_datetime(s[iso], errors="coerce")
    if (~iso).any():
        dh[~iso] = pd.to_datetime(s[~iso], errors="coerce", dayfirst=True)
    return dh


def main():
    eng = create_engine(DB_URL)
    arquivos = [(ano, DIR_CSV / PADRAO_ARQUIVO.format(ano=ano)) for ano in ANOS]
    faltando = [str(p) for _, p in arquivos if not p.exists()]
    if faltando:
        sys.exit("Arquivos não encontrados:\n  " + "\n  ".join(faltando))

    # 1) união dos cabeçalhos (o layout pode mudar entre anos)
    uniao = []
    for ano, p in arquivos:
        cab, _ = ler_csv(p, nrows=0)
        for c in cab.columns:
            if c not in uniao:
                uniao.append(c)
    print(f"Campos distintos nos cabeçalhos 2017-2024: {len(uniao)}  (TCC afirma 31)")
    print(uniao)

    cols_ddl = ", ".join(f'"{c}" text' for c in uniao)
    with eng.begin() as conn:
        conn.execute(text(
            "CREATE TABLE IF NOT EXISTS raw.datatran_primario ("
            "rid bigserial PRIMARY KEY, "
            "id_arquivo int NOT NULL REFERENCES prov.arquivo_origem, "
            "linha_arquivo int NOT NULL, "
            f"{cols_ddl}, latitude_num double precision, longitude_num double precision, "
            "data_hora timestamp)"))

    # 2) carga por arquivo (uma transação por arquivo)
    for ano, p in arquivos:
        sha = sha256_arquivo(p)
        with eng.begin() as conn:
            if conn.execute(text("SELECT 1 FROM prov.arquivo_origem WHERE sha256 = :h"), {"h": sha}).scalar():
                print(f"{p.name}: já carregado, pulando")
                continue
            df, enc = ler_csv(p)
            n_lin, n_col = df.shape
            id_arq = conn.execute(text(
                "INSERT INTO prov.arquivo_origem (ano, nome_arquivo, url, data_download, encoding, "
                "n_linhas, n_colunas, colunas, sha256) VALUES (:a, :n, :u, :d, :e, :nl, :nc, :c, :h) "
                "RETURNING id_arquivo"),
                {"a": ano, "n": p.name, "u": URL_POR_ANO.get(ano) or None,
                 "d": dt.datetime.fromtimestamp(p.stat().st_mtime, dt.timezone.utc),
                 "e": enc, "nl": n_lin, "nc": n_col, "c": list(df.columns), "h": sha}).scalar_one()
            e_arq = entidade(conn, "arquivo", p.name, id_arq)
            ida = abrir_atividade(conn, ETAPA, __file__, {"ano": ano, "sha256": sha, "encoding": enc},
                                  entrada=None, saida="raw.datatran_primario", id_entrada_pronto=e_arq)

            for c in uniao:
                if c not in df:
                    df[c] = pd.NA
            df["id_arquivo"] = id_arq
            df["linha_arquivo"] = range(1, n_lin + 1)
            # Conversões tipadas ficam em colunas à parte; o texto publicado é preservado.
            df["latitude_num"] = para_float(df["latitude"]) if "latitude" in df else pd.NA
            df["longitude_num"] = para_float(df["longitude"]) if "longitude" in df else pd.NA
            df["data_hora"] = data_hora(df)
            ordem = TECNICAS + uniao + ["latitude_num", "longitude_num", "data_hora"]

            buf = io.StringIO()
            df[ordem].to_csv(buf, index=False, header=False, na_rep="")
            buf.seek(0)
            cols_sql = ", ".join(f'"{c}"' for c in ordem)
            cur = conn.connection.cursor()
            cur.copy_expert(f"COPY raw.datatran_primario ({cols_sql}) FROM STDIN WITH (FORMAT csv)", buf)
            fechar_atividade(conn, ida, n_lin)
            print(f"{p.name}: {n_lin} linhas, {n_col} colunas, enc={enc}, "
                  f"data_hora inválida={int(df['data_hora'].isna().sum())}")

    # 3) imutabilidade (Seção 3.2): bloqueia UPDATE/DELETE/TRUNCATE na tabela primária
    with eng.begin() as conn:
        conn.execute(text(
            "CREATE OR REPLACE FUNCTION raw.bloquear_alteracao() RETURNS trigger AS $$ "
            "BEGIN RAISE EXCEPTION 'raw.datatran_primario é imutável'; END $$ LANGUAGE plpgsql"))
        conn.execute(text("DROP TRIGGER IF EXISTS trg_imutavel ON raw.datatran_primario"))
        conn.execute(text("CREATE TRIGGER trg_imutavel BEFORE UPDATE OR DELETE ON raw.datatran_primario "
                          "FOR EACH ROW EXECUTE FUNCTION raw.bloquear_alteracao()"))
        conn.execute(text("DROP TRIGGER IF EXISTS trg_imutavel_trunc ON raw.datatran_primario"))
        conn.execute(text("CREATE TRIGGER trg_imutavel_trunc BEFORE TRUNCATE ON raw.datatran_primario "
                          "FOR EACH STATEMENT EXECUTE FUNCTION raw.bloquear_alteracao()"))
    print("Tabela primária travada contra alterações.")


if __name__ == "__main__":
    main()
