import os
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from logger import get_logger

from dotenv import load_dotenv

load_dotenv()

def get_engine() -> Engine:

    logger = get_logger(__name__)

    """
    Cria e retorna a conexão (engine) com o Postgres.
    As credenciais são buscadas de variáveis de ambiente

    :return: Engine
    """
    user = os.getenv("DB_USER","postgres")
    password = os.getenv("DB_PASSWORD", "postgres")
    host = os.getenv("DB_HOST","localhost")
    port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "loretto_dw")

    url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db_name}"

    logger.info(f"Conectando ao banco {db_name} em {host}:{port}...")

    return create_engine(url, pool_pre_ping=True)


