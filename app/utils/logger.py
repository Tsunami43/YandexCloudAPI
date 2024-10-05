import os
from loguru import logger


def setup_logger():

    # Проверка существования директории для логов
    os.makedirs("logs", exist_ok=True)

    logger.add(
        "logs/app.log",
        rotation="1 week",
        level="DEBUG",
        format="{time} {level} {message}",
        backtrace=True,
        diagnose=True,
    )
