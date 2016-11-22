# coding: utf-8

import datetime
import json
import logging
import logging.config
import os
import re
import tempfile


BASE_DIR = os.path.abspath(os.path.dirname(__name__))
DEFAULT_CURRENCY = "usd"
DEFAULT_PARSER_MODULE = "belgazprombank_parser"
DEFAULT_PARSER_NAME = "bgp"
PARSERS_DIR = os.path.join("bot", "parsers")
PIDFILE = os.path.join(tempfile.gettempdir(), "telegrambot.pid")
LOCALIZATION_PATH = os.path.join(BASE_DIR, "locale")

API_ENV_NAME = 'BANK_BOT_AP_TOKEN'
CACHE_EXPIRACY_MINUTES = 60
IMAGES_FOLDER = "img"
USER_BANK_SELECTION_CACHE = {}

DATE_REGEX = re.compile(r"-d(?P<date_diff>[\d]+)")

# logging settings
LOGGER_NAME = "bankparser"
LOGGING_SETTINGS_FILE = os.path.join(BASE_DIR, "logging.json")

if os.path.exists(LOGGING_SETTINGS_FILE):
    with open(LOGGING_SETTINGS_FILE) as f:
        logging.config.dictConfig(json.load(f))
logger = logging.getLogger(LOGGER_NAME)


DENOMINATION_DATE = datetime.date(year=2016, month=7, day=1)
DENOMINATION_MULTIPLIER = 10000
