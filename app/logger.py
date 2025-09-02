import logging
import sys
import os


def get_logger(name: str) -> logging.Logger:
    """
    Cria e retorna um logger configurado.
    - Saída no stdout
    - Nível default = INFO
    - Formato com timestamp e nível
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(os.getenv("LOGGING_LEVE", logging.INFO))

    return logger
