#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2017-10-24 11:17:01
# @Author  : 郝天飞/Talen Hao (talenhao@gmail.com)
# @Link    : talenhao.github.io
# @Version : $Id$


import configparser
# for log >>
import logging
import os
from serconevo.log4p import log4p

SCRIPT_NAME = os.path.basename(__file__)
pLogger = log4p.GetLogger(SCRIPT_NAME, logging.DEBUG).get_l()
# log end <<
config_file = os.path.dirname(os.path.abspath(__file__)) + '/config.ini'


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
            pLogger.error("正则匹配配置文件语法有误，检查配置文件！")
        else:
            return python_config_parser


python_config_parser = SCEConfigParser(config_file).config_parser()
