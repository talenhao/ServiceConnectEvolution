#!/bin/env python
# -*- coding:utf-8 -*-

import pymysql
import datetime
import sys
import configparser

# for log >>
import logging
import os
import log4p

SCRIPT_NAME = os.path.basename(__file__)
pLogger = log4p.GetLogger(SCRIPT_NAME, logging.DEBUG).get_l()
# log end <<


def exception(e):
    pLogger.exception(e)
    sys.exit()


class SCEConfigParser:
    def __init__(self, config_file='config.ini'):
        self.config_file = config_file
        pLogger.debug("使用配置文件 {} ".format(self.config_file))

    def config_parser(self):
        # with open(self.config_file,mode='r') as self.fp:
        #     self.python_config_parser.read_file(self.fp)
        try:
            python_config_parser = configparser.ConfigParser()
            python_config_parser.read(self.config_file)
        except configparser.ParsingError:
            exception("正则匹配配置文件语法有误，检查配置文件！")
        return python_config_parser


class DbInitConnect(object):
    """
    数据库初始化及连接，游标
    """
    # 初始化基本变量
    def __init__(self):
        self.python_config_parser = SCEConfigParser().config_parser()
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
        self.cursor = self.db_cursor()

    # 连接数据库
    def db_connect(self):
        connect = pymysql.connect(**self.config)
        # 返回指针
        return connect

    # 游标
    def db_cursor(self):
        cursor = self.connect.cursor()
        return cursor

    def finally_close_all(self):
        """
        关闭游标，关闭连接。
        :return:
        """
        self.cursor.close()
        self.connect.close()

    def show_databases(self):
        sql_cmd = 'show create database yed_collect'
        try:
            self.cursor.execute(sql_cmd)
        except:
            pLogger.error('数据库操作失败!')
        finally:
            for row in self.cursor.fetchall():
                pLogger.info(row)
