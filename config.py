import sys

from loguru import logger

logger.remove()
logger.add(sys.stderr, format='<green>[{elapsed}]</green> [{file}] > <level>{message}</level>')
logger.add('logs/app.log', mode='w', format='[{elapsed}] [{file}] > {message}')