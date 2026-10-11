"""Camada de proveniência (PROV): agente, entidade, atividade + utilitários."""
import hashlib, json, subprocess
from pathlib import Path
from sqlalchemy import text

COLUNAS_TECNICAS = {"rid", "id_arquivo", "linha_arquivo", "latitude_num", "longitude_num",
                    "data_hora", "coord_status", "validacao_geo", "geom_4674", "geom_5880"}


def sha256_arquivo(caminho, bloco=1 << 20):
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        while chunk := f.read(bloco):
            h.update(chunk)
    return h.hexdigest()


def versao_git():
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"],
                                       stderr=subprocess.DEVNULL, text=True).strip()
    except Exception:
        return "sem-git"


def colunas_publicadas(conn):
    """Campos publicados pela PRF (exclui colunas técnicas criadas pelo pipeline)."""
    r = conn.execute(text("SELECT column_name FROM information_schema.columns "
                          "WHERE table_schema='raw' AND table_name='datatran_primario' "
                          "ORDER BY ordinal_position"))
    return [c for (c,) in r if c not in COLUNAS_TECNICAS]


def agente(conn, script):
    caminho = Path(script)
    return conn.execute(text(
        "INSERT INTO prov.agente (script, versao, sha256_codigo) VALUES (:s, :v, :h) "
        "ON CONFLICT (script, versao, sha256_codigo) DO UPDATE SET script = EXCLUDED.script "
        "RETURNING id_agente"),
        {"s": caminho.name, "v": versao_git(), "h": sha256_arquivo(caminho)}).scalar_one()


def entidade(conn, tipo, nome, id_arquivo=None):
    return conn.execute(text(
        "INSERT INTO prov.entidade (tipo, nome, id_arquivo) VALUES (:t, :n, :a) "
        "ON CONFLICT (nome) DO UPDATE SET nome = EXCLUDED.nome RETURNING id_entidade"),
        {"t": tipo, "n": nome, "a": id_arquivo}).scalar_one()


def abrir_atividade(conn, etapa, script, parametros, entrada=None, saida=None,
                    tipo_entrada="tabela", id_entrada_pronto=None):
    id_ag = agente(conn, script)
    e_in = id_entrada_pronto or (entidade(conn, tipo_entrada, entrada) if entrada else None)
    e_out = entidade(conn, "tabela", saida) if saida else None
    return conn.execute(text(
        "INSERT INTO prov.atividade (etapa, id_agente, parametros, id_entidade_entrada, "
        "id_entidade_saida, inicio) VALUES (:e, :a, CAST(:p AS jsonb), :i, :o, clock_timestamp()) "
        "RETURNING id_atividade"),
        {"e": etapa, "a": id_ag, "p": json.dumps(parametros, default=str), "i": e_in, "o": e_out}).scalar_one()


def fechar_atividade(conn, id_atividade, n_linhas=None):
    conn.execute(text("UPDATE prov.atividade SET fim = clock_timestamp(), n_linhas_afetadas = :n "
                      "WHERE id_atividade = :i"), {"n": n_linhas, "i": id_atividade})


def exigir_nao_executada(conn, etapa):
    n = conn.execute(text("SELECT count(*) FROM prov.atividade WHERE etapa = :e"), {"e": etapa}).scalar()
    if n:
        raise SystemExit(f"A etapa {etapa} já foi executada. Rode 03_duplicatas.py --refazer e repita "
                         f"as etapas seguintes (o log é apagado nesse caso).")
