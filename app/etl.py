import pandas as pd

from sqlalchemy.engine import Engine
from sqlalchemy import text
from db import get_engine   # 👈 precisa desse import
from logger import get_logger
from datetime import datetime

logger = get_logger(__name__)

def load_staging(df: pd.DataFrame, engine: Engine, table_name: str = "staging_lancamentos") -> None:
    """
    Carrega DataFrame em tabela de staging no Postgres.
    Se a tabela não existir, será criada automaticamente.
    """
    df.to_sql(table_name, engine, if_exists="replace", index=False)

    logger.info(f"{len(df)} registros inseridos na tabela {table_name}")

def load_dim_tempo(engine: Engine, df: pd.DataFrame):
    """
    Popula a dim_tempo a partir da coluna 'data' (MM/YYYY).
    """
    df_tempo = (
        df["data"]
        .dropna()
        .drop_duplicates()
        .apply(lambda x: datetime.strptime(x, "%m/%Y"))
        .to_frame(name="data")
    )
    df_tempo["ano"] = df_tempo["data"].dt.year
    df_tempo["mes"] = df_tempo["data"].dt.month
    df_tempo["semana"] = df_tempo["data"].dt.isocalendar().week
    df_tempo["data_inicio"] = df_tempo["data"].dt.to_period("M").dt.start_time
    df_tempo["data_fim"] = df_tempo["data"].dt.to_period("M").dt.end_time

    df_tempo = df_tempo[["ano", "mes", "semana", "data_inicio", "data_fim"]]

    df_tempo.to_sql("dim_tempo", engine, if_exists="append", index=False)
    logger.info(f"{len(df_tempo)} registros inseridos em dim_tempo")


def load_dim_tipo(engine: Engine):
    """
    Popula a dim_tipo a partir da staging, evitando duplicatas.
    """
    sql = """
    INSERT INTO dim_tipo (nome_tipo)
    SELECT DISTINCT sl."Tipo"
    FROM staging_lancamentos sl
    ON CONFLICT (nome_tipo) DO NOTHING;
    """
    with engine.begin() as conn:
        conn.execute(text(sql))
    logger.info("dim_tipo populada com sucesso")


def load_dim_grupo(engine: Engine):
    """
    Popula a dim_grupo vinculada à dim_tipo, evitando duplicatas.
    """
    sql = """
    INSERT INTO dim_grupo (id_tipo, nome_grupo)
    SELECT dt.id_tipo, sl."Grupo"
    FROM staging_lancamentos sl
    JOIN dim_tipo dt ON dt.nome_tipo = sl."Tipo"
    ON CONFLICT (id_tipo, nome_grupo) DO NOTHING;
    """
    with engine.begin() as conn:
        conn.execute(text(sql))
    logger.info("dim_grupo populada com sucesso")


def load_dim_categoria(engine: Engine):
    """
    Popula a dim_categoria vinculada à dim_grupo, evitando duplicatas.
    """
    sql = """
    INSERT INTO dim_categoria (id_grupo, nome_categoria)
    SELECT dg.id_grupo, sl."Categoria"
    FROM staging_lancamentos sl
    JOIN dim_tipo dt ON dt.nome_tipo = sl."Tipo"
    JOIN dim_grupo dg ON dg.nome_grupo = sl."Grupo" AND dg.id_tipo = dt.id_tipo
    ON CONFLICT (id_grupo, nome_categoria) DO NOTHING;
    """
    with engine.begin() as conn:
        conn.execute(text(sql))
    logger.info("dim_categoria populada com sucesso")


def load_fato_lancamento(engine: Engine):
    """
    Popula a fato_lancamento usando as dimensões já carregadas.
    Se já existir, ignora.
    """
    sql = """
    INSERT INTO fato_lancamento (id_tipo, id_grupo, id_categoria, id_tempo, descricao, valor, id_hash)
    SELECT
        dt.id_tipo,
        dg.id_grupo,
        dc.id_categoria,
        dtmp.id_tempo,
        sl."Descrição",
        sl.valor,
        sl.id_hash
    FROM staging_lancamentos sl
    JOIN dim_tipo dt ON dt.nome_tipo = sl."Tipo"
    JOIN dim_grupo dg ON dg.nome_grupo = sl."Grupo" AND dg.id_tipo = dt.id_tipo
    JOIN dim_categoria dc ON dc.nome_categoria = sl."Categoria" AND dc.id_grupo = dg.id_grupo
    JOIN dim_tempo dtmp ON dtmp.ano = SPLIT_PART(sl.data, '/', 2)::int
                       AND dtmp.mes = SPLIT_PART(sl.data, '/', 1)::int
    ON CONFLICT (id_hash) DO NOTHING;
    """
    with engine.begin() as conn:
        conn.execute(text(sql))
    logger.info("fato_lancamento populada com sucesso")


def run_etl():
    engine = get_engine()
    df = pd.read_sql("SELECT * FROM staging_lancamentos", engine)

    logger.info("Iniciando ETL...")

    load_dim_tempo(engine, df)   # precisa do df
    load_dim_tipo(engine)        # não precisa
    load_dim_grupo(engine)       # não precisa
    load_dim_categoria(engine)   # não precisa
    load_fato_lancamento(engine) # não precisa

    logger.info("ETL concluído com sucesso!")

