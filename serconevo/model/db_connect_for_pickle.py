#!/bin/env python
# -*- coding:utf-8 -*-

import sys
import configparser

# for log >>
import logging
import os
from serconevo.log4p import log4p

SCRIPT_NAME = os.path.basename(__file__)
pLogger = log4p.GetLogger(SCRIPT_NAME, logging.DEBUG).get_l()
config_file = os.path.dirname(os.path.abspath(__file__)) + '/config4pickle.ini'
pLogger.debug("\n" * 50)
pLogger.debug("config file is {}".format(config_file))
# log end <<


def exception(e):
    pLogger.exception(e)
    sys.exit()


class SCEConfigParser:
    def __init__(self, config_file=config_file):
        self.config_file = config_file
        pLogger.debug("Use config file: {} ".format(self.config_file))

    def config_parser(self):
        # with open(self.config_file,mode='r') as self.fp:
        #     self.python_config_parser.read_file(self.fp)
        try:
            python_config_parser = configparser.ConfigParser()
            python_config_parser.read(self.config_file)
        except configparser.ParsingError:
            exception("正则匹配配置文件语法有误，检查配置文件！")
        else:
            return python_config_parser


class DbInitConnect(object):
    """
    数据库初始化及连接，游标
    """
    # 初始化基本变量
    def __init__(self):
        self.python_config_parser = SCEConfigParser().config_parser()
