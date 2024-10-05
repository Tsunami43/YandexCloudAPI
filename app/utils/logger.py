from loguru import logger


def setup_logger():
    logger.add(
        "app.log",
        rotation="1 MB",
        level="DEBUG",
        format="{time} {level} {message}",
        backtrace=True,
        diagnose=True,
    )
