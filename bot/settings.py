# coding: utf-8

import logging

LOGGER_NAME = "bankparser"

DEFAULT_CURRENCY = "usd"
DEFAULT_PARSER_NAME = "bgp"
PARSERS_DIR = "parsers"
DEFAULT_PARSER_MODULE = "belgazprombank_parser"

logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO)
logger = logging.getLogger(LOGGER_NAME)
