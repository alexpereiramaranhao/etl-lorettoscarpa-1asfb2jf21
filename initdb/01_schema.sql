-- Cria banco para o loretto_dw
CREATE DATABASE loretto_dw
    WITH OWNER = postgres
    ENCODING = 'UTF8'
    CONNECTION LIMIT = -1;

\c loretto_dw


--------------------------------------------------------------------------------
-- Dimensão Tipo
--------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_tipo (
                                        id_tipo SERIAL PRIMARY KEY,
                                        nome_tipo VARCHAR(100) NOT NULL UNIQUE   -- 👈 garante unicidade
    );

--------------------------------------------------------------------------------
-- Dimensão Classificacao
--------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_classificacao (
                                        id_classificacao SERIAL PRIMARY KEY,
                                        nome_classificacao VARCHAR(256) NOT NULL UNIQUE   -- 👈 garante unicidade
    );

--------------------------------------------------------------------------------
-- Dimensão Grupo
--------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_grupo (
                                         id_grupo SERIAL PRIMARY KEY,
                                         id_tipo INT NOT NULL,
                                         nome_grupo VARCHAR(150) NOT NULL,
    CONSTRAINT fk_grupo_tipo FOREIGN KEY (id_tipo)
    REFERENCES dim_tipo (id_tipo),
    CONSTRAINT uq_grupo UNIQUE (id_tipo, nome_grupo)  -- 👈 deduplicação
    );

--------------------------------------------------------------------------------
-- Dimensão Categoria
--------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_categoria (
                                             id_categoria SERIAL PRIMARY KEY,
                                             id_grupo INT NOT NULL,
                                             nome_categoria VARCHAR(150) NOT NULL,
    CONSTRAINT fk_categoria_grupo FOREIGN KEY (id_grupo)
    REFERENCES dim_grupo (id_grupo),
    CONSTRAINT uq_categoria UNIQUE (id_grupo, nome_categoria)  -- 👈 deduplicação
    );

--------------------------------------------------------------------------------
-- Dimensão Tempo
--------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_tempo (
                                         id_tempo SERIAL PRIMARY KEY,
                                         ano INT NOT NULL,
                                         mes INT NOT NULL,
                                         semana INT,
                                         data_inicio DATE NOT NULL,
                                         data_fim DATE NOT NULL

    );

--------------------------------------------------------------------------------
-- Fato Lançamento
--------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fato_lancamento (
                                               id_lancamento SERIAL PRIMARY KEY,
                                               id_tipo INT NOT NULL,
                                               id_grupo INT NOT NULL,
                                               id_categoria INT NOT NULL,
                                               id_tempo INT NOT NULL,
                                               id_classificacao INT NOT NULL,
                                               descricao VARCHAR(255),
    valor NUMERIC(15,2) NOT NULL,
    id_hash TEXT NOT NULL UNIQUE,
    CONSTRAINT fk_fato_tipo FOREIGN KEY (id_tipo)
    REFERENCES dim_tipo (id_tipo),
    CONSTRAINT fk_fato_grupo FOREIGN KEY (id_grupo)
    REFERENCES dim_grupo (id_grupo),
    CONSTRAINT fk_fato_classificacao FOREIGN KEY (id_classificacao)
    REFERENCES dim_classificacao (id_classificacao), -- ✅ CORRIGIDO
    CONSTRAINT fk_fato_categoria FOREIGN KEY (id_categoria)
    REFERENCES dim_categoria (id_categoria),
    CONSTRAINT fk_fato_tempo FOREIGN KEY (id_tempo)
    REFERENCES dim_tempo (id_tempo)
    );

