# coding: utf-8

import logging

LOGGER_NAME = "bankparser"

logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO)
logger = logging.getLogger(LOGGER_NAME)
