import os

MONGO_HOST = os.environ.get('TELEGRAM_MONGODB_HOST')
MONGO_PORT = os.environ.get('TELEGRAM_MONGODB_PORT')
MONGO_DATABASE = os.environ.get('TELEGRAM_MONGODB_DB')
MONGO_COLLECTION = os.environ.get('TELEGRAM_MONGODB_COLLECTION')
MONGO_USER = os.environ.get('TELEGRAM_MONGODB_USER')
MONGO_PASSWORD = os.environ.get('TELEGRAM_MONGODB_PASSWORD')
