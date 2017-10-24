#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2017-10-24 11:26:56
# @Author  : 郝天飞/Talen Hao (talenhao@gmail.com)
# @Link    : talenhao.github.io
# @Version : $Id$


import sys
# for log >>
import logging
import os
from serconevo.log4p import log4p

SCRIPT_NAME = os.path.basename(__file__)
pLogger = log4p.GetLogger(SCRIPT_NAME, logging.DEBUG).get_l()
# log end <<


def exception(e):
    pLogger.exception(e)
    sys.exit()
