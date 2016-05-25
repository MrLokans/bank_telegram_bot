import os

REDIS_HOST = os.environ.get('TELEGRAM_REDIS_HOST', 'localhost')
REDIS_PORT = int(os.environ.get('TELEGRAM_REDIS_PORT', '27017'))
REDIS_DB = int(os.environ.get('TELEGRAM_REDIS_DB', '0'))
