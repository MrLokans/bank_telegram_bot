import os

REDIS_HOST = os.environ.get('TELEGRAM_REDIS_HOST', 'localhost')
REDIS_PORT = int(os.environ.get('TELEGRAM_REDIS_PORT', '6379'))
REDIS_DB = int(os.environ.get('TELEGRAM_REDIS_DB', '0'))
