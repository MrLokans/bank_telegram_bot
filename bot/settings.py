# coding: utf-8

import os
import logging
import tempfile

LOGGER_NAME = "bankparser"

BASE_DIR = os.path.abspath(os.path.dirname(__name__))
DEFAULT_CURRENCY = "usd"
DEFAULT_PARSER_MODULE = "belgazprombank_parser"
DEFAULT_PARSER_NAME = "bgp"
PARSERS_DIR = "parsers"
PIDFILE = os.path.join(tempfile.gettempdir(), "telegrambot.pid")
LOCALIZATION_PATH = os.path.join(BASE_DIR, "locale")

logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO)
logger = logging.getLogger(LOGGER_NAME)
