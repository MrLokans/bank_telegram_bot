# coding: utf-8

import os
import logging

LOGGER_NAME = "bankparser"

DEFAULT_CURRENCY = "usd"
DEFAULT_PARSER_NAME = "bgp"
PARSERS_DIR = "parsers"
DEFAULT_PARSER_MODULE = "belgazprombank_parser"
BASE_DIR = os.path.abspath(os.path.dirname(__name__))
LOCALIZATION_PATH = os.path.join(BASE_DIR, "localization")

logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO)
logger = logging.getLogger(LOGGER_NAME)
