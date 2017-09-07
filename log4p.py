#!/usr/bin/env python
# -*- coding:UTF-8 -*-

import logging
import logging.config
import json

__author__ = "Talen Hao(天飞)<talenhao@gmail.com>"
__status__ = "product"
__last_date__ = "2017.08.21"
__version__ = __last_date__
__create_date__ = "2017.08.21"


class GetLogger:
    def __init__(self, logger_name, logging_level="debug"):
        self.logger_name = logger_name
        self.logging_level = logging_level

    def get_l(self):
        # Create a logger
        agent_logger = logging.getLogger(self.logger_name)
        agent_logger.setLevel(self.logging_level)
        with open("log4p.json", 'r') as logging_configuration_file:
            config_dict = json.load(logging_configuration_file)
            logging.config.dictConfig(config_dict)
        return agent_logger
