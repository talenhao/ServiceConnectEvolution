#!/bin/env python
# -*- coding:utf-8 -*-

import pymysql.connections
import pymysql.err
import pymysql.cursors
import configparser

# for log >>
import logging
import os
from serconevo.log4p import log4p
from serconevo.configprocess import config_file
from serconevo.errorprocess import exception
from serconevo.configprocess import SCEConfigParser

SCRIPT_NAME = os.path.basename(__file__)
pLogger = log4p.GetLogger(SCRIPT_NAME, logging.DEBUG).get_l()
# log end <<


class DbInitConnect(object):
    """
    数据库初始化及连接，游标
    """
    # 初始化基本变量

    def __init__(self, config_file=config_file):
        self.python_config_parser = SCEConfigParser(config_file).config_parser()
        try:
            host = self.python_config_parser.get("DB", "host")
            pLogger.debug("type of port {} {}".format(type(host), host))
            port = self.python_config_parser.get("DB", "port")
            port = int(port)
            pLogger.debug("type of port {}".format(type(port)))
            password = self.python_config_parser.get("DB", "password")
            username = self.python_config_parser.get("DB", "username")
            db = self.python_config_parser.get("DB", "db_name")
            self.config = {
                'host': host,
                'port': port,
                'user': username,
                'password': password,
                'db': db
            }
            pLogger.debug(self.config)
        except configparser.NoSectionError as e:
            exception(e)
        except configparser.NoOptionError as e:
            exception(e)
        self.connect = self.db_connect()
        self.ssdictcursor = self.db_sscursor()
        self.dictcursor = self.db_cursor()

    # 连接数据库
    def db_connect(self):
        try:
            connect = pymysql.connections.Connection(**self.config)
        except(pymysql.err.OperationalError, OSError) as e:
            exception(e)
        # 返回指针
        else:
            return connect

    # 游标
    def db_sscursor(self):
        # cursor = self.connect.cursor()
        cursor = pymysql.cursors.SSDictCursor(self.connect)
        return cursor

    def db_cursor(self):
        # cursor = self.connect.cursor()
        cursor = pymysql.cursors.DictCursor(self.connect)
        return cursor

    def finally_close_all(self):
        """
        关闭游标，关闭连接。
        :return:
        """
        self.ssdictcursor.close()
        self.dictcursor.close()
        self.connect.close()

    def show_databases(self):
        sql_cmd = 'show create database yed_collect'
        try:
            self.ssdictcursor.execute(sql_cmd)
        except:
            pLogger.error('数据库操作失败!')
        finally:
            for row in self.cursor.fetchall():
                pLogger.info(row)
