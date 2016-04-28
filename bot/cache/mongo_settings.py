import os

MONGO_HOST = os.environ.get('TELEGRAM_MONGODB_HOST', 'localhost')
MONGO_PORT = int(os.environ.get('TELEGRAM_MONGODB_PORT', 27017))
MONGO_DATABASE = os.environ.get('TELEGRAM_MONGODB_DB', 'telegrambot')
MONGO_COLLECTION = os.environ.get('TELEGRAM_MONGODB_COLLECTION', 'currencies')
MONGO_USER = os.environ.get('TELEGRAM_MONGODB_USER')
MONGO_PASSWORD = os.environ.get('TELEGRAM_MONGODB_PASSWORD')
