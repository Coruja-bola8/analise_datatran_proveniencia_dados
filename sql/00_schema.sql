-- Execute uma vez:  psql -d datatran -f sql/00_schema.sql
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE SCHEMA IF NOT EXISTS prov;
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS clean;
CREATE SCHEMA IF NOT EXISTS aux;

-- ===== CAMADA DE ORIGEM (dados primários, Seção 3.3) =====
CREATE TABLE IF NOT EXISTS prov.arquivo_origem (
  id_arquivo     serial PRIMARY KEY,
  ano            int  NOT NULL,
  nome_arquivo   text NOT NULL,
  url            text,
  data_download  timestamptz,          -- aproximada pela data de modificação do arquivo local
  encoding       text,
  n_linhas       bigint NOT NULL,
  n_colunas      int NOT NULL,
  colunas        text[] NOT NULL,
  sha256         text NOT NULL UNIQUE, -- identificação do conteúdo (hash)
  registrado_em  timestamptz NOT NULL DEFAULT now()
);

-- ===== MODELO PROV (Seção 2.3): agente, entidade, atividade =====
-- agente = script executado, com versão
CREATE TABLE IF NOT EXISTS prov.agente (
  id_agente     serial PRIMARY KEY,
  script        text NOT NULL,
  versao        text NOT NULL,         -- commit git, se houver
  sha256_codigo text NOT NULL,         -- hash do arquivo do script
  UNIQUE (script, versao, sha256_codigo)
);
-- entidade = arquivo publicado pela PRF / tabela
CREATE TABLE IF NOT EXISTS prov.entidade (
  id_entidade serial PRIMARY KEY,
  tipo        text NOT NULL CHECK (tipo IN ('arquivo','tabela')),
  nome        text NOT NULL UNIQUE,
  id_arquivo  int REFERENCES prov.arquivo_origem
);
-- atividade = etapa de limpeza
CREATE TABLE IF NOT EXISTS prov.atividade (
  id_atividade        serial PRIMARY KEY,
  etapa               text NOT NULL,
  id_agente           int NOT NULL REFERENCES prov.agente,
  parametros          jsonb NOT NULL DEFAULT '{}',
  id_entidade_entrada int REFERENCES prov.entidade,
  id_entidade_saida   int REFERENCES prov.entidade,
  inicio              timestamptz NOT NULL DEFAULT now(),
  fim                 timestamptz,
  n_linhas_afetadas   bigint
);

-- ===== CAMADA DE MODIFICAÇÃO (dados derivados, Seção 3.3 a-e) =====
CREATE TABLE IF NOT EXISTS prov.modificacao (
  id_mod          bigserial PRIMARY KEY,
  rid             bigint NOT NULL,     -- (a) registro na tabela primária
  campo           text,                -- (b)
  operacao        text NOT NULL CHECK (operacao IN ('IMPUTACAO','DESCARTE','PADRONIZACAO','MARCACAO')),
  valor_original  text,                -- (c)
  valor_novo      text,
  rid_relacionado bigint,              -- descarte: registro mantido
  regra           text NOT NULL,       -- (d)
  parametros      jsonb NOT NULL DEFAULT '{}',
  id_atividade    int NOT NULL REFERENCES prov.atividade,  -- (d) etapa; (e) versão via atividade->agente
  executado_em    timestamptz NOT NULL DEFAULT now()       -- (e)
);
CREATE INDEX IF NOT EXISTS ix_mod_rid_campo ON prov.modificacao (rid, campo);
CREATE INDEX IF NOT EXISTS ix_mod_oper ON prov.modificacao (operacao, campo);
CREATE INDEX IF NOT EXISTS ix_mod_ativ ON prov.modificacao (id_atividade);

CREATE OR REPLACE VIEW prov.v_modificacao AS
SELECT m.id_mod, m.rid, m.campo, m.operacao, m.valor_original, m.valor_novo, m.rid_relacionado,
       a.etapa, m.regra, m.parametros, m.executado_em, g.script, g.versao AS versao_script
FROM prov.modificacao m
JOIN prov.atividade a ON a.id_atividade = m.id_atividade
JOIN prov.agente g ON g.id_agente = a.id_agente;

-- Relações em vocabulário PROV-DM
CREATE OR REPLACE VIEW prov.v_relacoes AS
SELECT a.etapa || '#' || a.id_atividade AS sujeito, 'used' AS relacao, e.nome AS objeto
  FROM prov.atividade a JOIN prov.entidade e ON e.id_entidade = a.id_entidade_entrada
UNION ALL
SELECT e.nome, 'wasGeneratedBy', a.etapa || '#' || a.id_atividade
  FROM prov.atividade a JOIN prov.entidade e ON e.id_entidade = a.id_entidade_saida
UNION ALL
SELECT a.etapa || '#' || a.id_atividade, 'wasAssociatedWith', g.script || '@' || g.versao
  FROM prov.atividade a JOIN prov.agente g ON g.id_agente = a.id_agente;

-- número da BR como inteiro ("116", "116.0" -> 116)
CREATE OR REPLACE FUNCTION aux.br_int(t text) RETURNS int LANGUAGE sql IMMUTABLE AS
$$ SELECT CASE WHEN trim(t) ~ '^[0-9]+(\.0+)?$' THEN split_part(trim(t), '.', 1)::int END $$;
