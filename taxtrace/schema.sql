-- Esquema do TaxTrace. Toda linha pertence a uma coleta (versão da base + data da coleta).
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS coletas (
    id              bigserial PRIMARY KEY,
    coletado_em     timestamptz NOT NULL UNIQUE,
    data_consulta   date NOT NULL,
    versao_app      text NOT NULL,
    versao_base     text NOT NULL,
    descricao_base  text NOT NULL,
    data_base       date NOT NULL,
    ambiente        text NOT NULL
);

CREATE TABLE IF NOT EXISTS artigos (
    coleta_id            bigint NOT NULL REFERENCES coletas ON DELETE CASCADE,
    numero               text NOT NULL,
    texto                text NOT NULL,
    hierarquia           jsonb NOT NULL,
    tem_trecho_riscado   boolean NOT NULL,
    PRIMARY KEY (coleta_id, numero)
);

CREATE TABLE IF NOT EXISTS alteracoes (
    coleta_id      bigint NOT NULL,
    artigo_numero  text NOT NULL,
    ordem          integer NOT NULL,
    tipo           text NOT NULL,
    norma          text,
    ano            integer,
    texto          text NOT NULL,
    PRIMARY KEY (coleta_id, artigo_numero, ordem),
    FOREIGN KEY (coleta_id, artigo_numero) REFERENCES artigos ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS classificacoes (
    coleta_id                   bigint NOT NULL REFERENCES coletas ON DELETE CASCADE,
    codigo                      text NOT NULL,
    cst                         text NOT NULL,
    cst_descricao               text,
    descricao                   text NOT NULL,
    descricao_tratamento        text NOT NULL,
    tipo_aliquota               text NOT NULL,
    nomenclatura                text NOT NULL,
    percentual_reducao_cbs      numeric NOT NULL,
    percentual_reducao_ibs_uf   numeric NOT NULL,
    percentual_reducao_ibs_mun  numeric NOT NULL,
    data_atualizacao            date NOT NULL,
    texto_curto                 text NOT NULL,
    hierarquia_referencia       text NOT NULL,
    regra_geral                 boolean NOT NULL,
    PRIMARY KEY (coleta_id, codigo)
);

CREATE TABLE IF NOT EXISTS ligacoes (
    coleta_id      bigint NOT NULL,
    codigo         text NOT NULL,
    artigo_numero  text NOT NULL,
    PRIMARY KEY (coleta_id, codigo, artigo_numero),
    FOREIGN KEY (coleta_id, codigo) REFERENCES classificacoes ON DELETE CASCADE,
    FOREIGN KEY (coleta_id, artigo_numero) REFERENCES artigos ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ncm (
    coleta_id  bigint NOT NULL REFERENCES coletas ON DELETE CASCADE,
    codigo     text NOT NULL,
    descricao  text NOT NULL,
    PRIMARY KEY (coleta_id, codigo)
);

-- Diferenças entre as próprias tabelas da fonte e citações sem artigo na lei.
CREATE TABLE IF NOT EXISTS divergencias (
    coleta_id  bigint NOT NULL REFERENCES coletas ON DELETE CASCADE,
    ordem      integer NOT NULL,
    descricao  text NOT NULL,
    PRIMARY KEY (coleta_id, ordem)
);


-- Colunas aditivas: coletas antigas sem proveniência não entram na busca.
ALTER TABLE coletas ADD COLUMN IF NOT EXISTS manifesto_sha256 text;
ALTER TABLE coletas ADD COLUMN IF NOT EXISTS fontes jsonb;

CREATE TABLE IF NOT EXISTS documentos_busca (
    coleta_id bigint NOT NULL,
    artigo_numero text NOT NULL,
    texto_ativo text NOT NULL,
    termos tsvector GENERATED ALWAYS AS (to_tsvector('portuguese', texto_ativo)) STORED,
    PRIMARY KEY (coleta_id, artigo_numero),
    FOREIGN KEY (coleta_id, artigo_numero) REFERENCES artigos ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS documentos_busca_termos ON documentos_busca USING gin(termos);

-- Versão 2 aditiva: preserva o índice original para reproduzir a base de comparação.
CREATE EXTENSION IF NOT EXISTS unaccent;
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_ts_config c JOIN pg_namespace n ON n.oid=c.cfgnamespace
    WHERE n.nspname='public' AND c.cfgname='taxtrace_portugues_v2'
  ) THEN
    CREATE TEXT SEARCH CONFIGURATION public.taxtrace_portugues_v2 (COPY = pg_catalog.portuguese);
    ALTER TEXT SEARCH CONFIGURATION public.taxtrace_portugues_v2
      ALTER MAPPING FOR asciiword, asciihword, hword_asciipart, word, hword, hword_part
      WITH public.unaccent, pg_catalog.portuguese_stem;
  END IF;
END $$;
ALTER TABLE documentos_busca ADD COLUMN IF NOT EXISTS termos_v2 tsvector
  GENERATED ALWAYS AS (
    setweight(to_tsvector('public.taxtrace_portugues_v2', left(texto_ativo, 600)), 'A') ||
    setweight(to_tsvector('public.taxtrace_portugues_v2', texto_ativo), 'D')
  ) STORED;
CREATE INDEX IF NOT EXISTS documentos_busca_termos_v2 ON documentos_busca USING gin(termos_v2);
