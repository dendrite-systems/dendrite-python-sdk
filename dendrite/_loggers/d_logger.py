import sys

from loguru import logger

logger.remove()
fmt = "<green>{time: HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <level>{message}</level>"
logger.add(sys.stderr, level="DEBUG", format=fmt)
