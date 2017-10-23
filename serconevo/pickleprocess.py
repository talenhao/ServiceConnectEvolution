#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2017-10-20 14:38:18
# @Author  : 郝天飞/Talen Hao (talenhao@gmail.com)
# @Link    : talenhao.github.io
# @Version : $Id$

from serconevo import identify_line
import pickle
from serconevo import graph_nodes_bin
from serconevo import work_dir

# for log >>
import logging
import os
from serconevo.log4p import log4p
SCRIPT_NAME = os.path.basename(__file__)
# log end <<
pLogger = log4p.GetLogger(SCRIPT_NAME, logging.DEBUG).get_l()


def pickle_to_file(var_object, dump_file):
    pLogger.debug("{}\n\
                  var_object is: \n\
                  {!r}".format(identify_line, var_object))
    if not os.path.exists(work_dir):
        pLogger.debug("work_dir {} is not exists, create it.".format(work_dir))
        os.makedirs(work_dir)
    with open(dump_file, 'wb') as dump:
        pickle.dump(var_object, dump, True)


def pickle_from_file(pickle_file):
    pLogger.debug("{} pickle_file is:{!r}".format(
        identify_line, pickle_file))
    with open(pickle_file, 'rb') as load_file:
        return pickle.load(load_file)


def graph_nodes_list():
    result = pickle_from_file(graph_nodes_bin)
    return result
