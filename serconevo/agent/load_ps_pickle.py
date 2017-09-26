# -*- coding: UTF-8 -*-

"""
Collect socket information.
Copyright (C) 2017-2027 Talen Hao. All Rights Reserved.
"""
# to-do: process p_cwd

# built-in
import re
import sys
import getopt
import datetime
import pickle
import uuid

# user module
from serconevo.model import db_connect

# for log >>
import logging
import os
from serconevo.log4p import log4p

SCRIPT_NAME = os.path.basename(__file__)
pLogger = log4p.GetLogger(SCRIPT_NAME, logging.DEBUG).get_l()
# log end <<


# ******************************************************
__author__ = "Talen Hao(天飞)<talenhao@gmail.com>"
__create_date__ = "2017.09.05"
__last_date__ = "2017.09.07"
__version__ = __last_date__
# ******************************************************

all_args = sys.argv[1:]
usage = '''
用法：
{0!r} [--命令选项] [参数]

eg:  python {0!r} -f /home/htf/pyproject/sce/ser_con_evo/serconevo/agent/00000000-0000-0000-0000-1c872c4207df  -c /home/htf/pyproject/sce/ser_con_evo/serconevo/model/config4pickle.ini

命令选项：
    --help, -h              帮助。
    --version, -V           输出版本号。
    --picklefile, -f        pickle file, use absolute path.
    --config, -c            config file, use absolute path.
'''.format(sys.argv[0])


def get_options():
    if len(all_args) >= 2:
        pLogger.debug("Command arguments: {!r}".format(str(all_args)))
    else:
        pLogger.error(usage)
        sys.exit()
    try:
        opts, args = getopt.getopt(all_args, "hVf:c:", ["help", "version", "picklefile=", "config="])
    except getopt.GetoptError:
        pLogger.error(usage)
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-h', "--help"):
            pLogger.info(usage)
            sys.exit()
        elif opt in ("-V", "--version"):
            print('Current version is {}'.format(__version__))
            pLogger.debug('Version %s', __version__)
            sys.exit()
        elif opt in ("-f", "--picklefile"):
            pLogger.info("picklefile file is {!r}".format(arg))
            picklefile = arg
        elif opt in ("-c", "--config"):
            pLogger.info("config file is {!r}".format(arg))
            config = arg
    return picklefile, config


identify_line = "=*=" * 20
config_file = get_options()[1]
db_con = db_connect.DbInitConnect(config_file=config_file)
config_parser = db_con.python_config_parser
service_listens_table = config_parser.get("TABLE", "listen_table")
service_connections_table = config_parser.get("TABLE", "connection_table")
pLogger.debug("service_listens_table is {!r}, service_connections_table is {!r}".format(service_listens_table, service_connections_table))


# python版本判断，帮助等装饰器。
def script_head(func):
    def warper(*args, **kwargs):
        if sys.version_info < (3, 4):
            pLogger.warning('友情提示：当前系统版本低于3.4，请升级python版本。')
            raise RuntimeError('At least Python 3.4 is required')
        pLogger.info("Script version: {!r}".format(__version__))
        return func(*args, **kwargs)
    return warper


def get_server_uuid():
    # server_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, __author__))
    # 使用'dmidecode'命令生成（不足：需要使用root权限）。后来发现uuid模块的getnode生成的uuid竟然跟'dmidecode'是一样的。
    # 参考http://stackoverflow.com/questions/2461141/get-a-unique-computer-id-in-python-on-windows-and-linux
    server_uuid = str(uuid.UUID(int=uuid.getnode()))
    pLogger.info("server_uuid is: %s", server_uuid)
    return server_uuid


# db commit
def db_commit(func):
    def warper(*args, **kwargs):
        # config_parser = db_connect.SCEConfigParser().config_parser()
        sql_cmd = func(*args, **kwargs)
        pLogger.debug("SQL_CMD is =====> {!r}  __________".format(sql_cmd))
        db_con.cursor.execute(sql_cmd)
        pLogger.info("=====> DB operation command result: {!r}".format(
            db_con.cursor.rowcount))
        db_con.connect.commit()
    return warper


# db close_all
def db_close(func):
    def warper(*args, **kwargs):
        func(*args, **kwargs)
        db_con.finally_close_all()
    return warper


def spend_time(func):
    def warper(*args, **kwargs):
        start_time = datetime.datetime.now()
        pLogger.debug("Time start %s", start_time)
        func(*args, **kwargs)
        end_time = datetime.datetime.now()
        pLogger.debug("Time over %s,spend %s", end_time, end_time - start_time)
    return warper


def process_before_insert_db(string):
    # process cmdline @,#... because it will raise error when insert mysql
    try:
        rcm = re.compile(r'[@#}{ ,"\']+')
        rcm_data = re.compile(r'data[0-9]?/')
        rcm_solr = re.compile(r'solr[/0-9]?/')
        for arg in range(len(string)):
            if rcm.search(string[arg]):
                string[arg] = re.sub(rcm, '_', string[arg])
            if rcm_data.search(string[arg]):
                string[arg] = re.sub(rcm_data, 'dataX/', string[arg])
            if rcm_solr.search(string[arg]):
                string[arg] = re.sub(rcm_solr, 'solrX/', string[arg])
    except re.error:
        pLogger.error("There has some error when convert {}.".format(string))
        exit()


@db_commit
def import2db(table, ip, port, p_name, p_pid, p_exe, p_cwd,
              p_cmdline, p_status,
              p_create_time, p_username,
              server_uuid, **kwargs):
    pLogger.debug("import2db kwargs is {!r}".format(kwargs))
    process_before_insert_db(p_cmdline)
    # 1 column_values create
    ip_column = ""
    port_column = ""
    columns_num = 0
    columns_list_process = ["p_name", "p_pid", "p_exe", "p_cwd", "p_cmdline",
                            "p_status", "p_create_time", "p_username",
                            "server_uuid"]
    values_list = [ip, port, p_name, p_pid, p_exe,
                   p_cwd, p_cmdline, p_status, p_create_time, p_username,
                   server_uuid]
    pLogger.debug("columns_list_process is {}, values_list is {}".format(
        columns_list_process, values_list))
    try:
        pLogger.debug("table is {!r}".format(table))
        if table == service_listens_table:
            ip_column = "l_ip"
            port_column = "l_port"
            columns_num = 11
            pLogger.debug("Table is {}, column_num is {}".format(
                service_listens_table, columns_num))
        elif table == service_connections_table and kwargs['local_ip']:
            ip_column = "c_ip"
            port_column = "c_port"
            columns_num = 12
            pLogger.debug("Table is {},"
                          "column_num is {}, append column.".format(
                              service_listens_table, columns_num))
            columns_list_process.append('local_ip')
            values_list.append(kwargs['local_ip'])
        else:
            pLogger.debug("No table, maybe something is error, check log search 'table is'.")
    except ValueError:
        pLogger.exception(
            "Please check the table name argument {}.".format(table))
        exit()
    else:
        if ip_column and port_column:
            columns_list_t_i_p = [ip_column, port_column]
            columns_list_t_i_p.extend(columns_list_process)
            pLogger.debug(
                "columns_list_t_i_p is : {!r}, type {!r}".
                format(columns_list_t_i_p, type(columns_list_t_i_p)))
            # 2 SQL create
            columns_str = ','.join(
                ['{1' + str([i]) + '}' for i in range(columns_num)])
            values_str = ",".join(
                ['"{2' + str([i]) + '}"' for i in range(columns_num)])
            pLogger.debug("columns_str is : {!r}, values_str is : {!r} .".
                          format(columns_str, values_str))
            sql_format_str = 'INSERT ignore INTO {0} (' + \
                columns_str + ') VALUES (' + values_str + ')'
            pLogger.debug("sql_format_str is : {!r}".format(sql_format_str))
            sql_cmd = sql_format_str.format(
                table, columns_list_t_i_p, values_list)
            pLogger.debug("_sql is : {!r}".format(sql_cmd))
            pLogger.debug("{} insert database operation command: {}"
                          .format(p_exe, sql_cmd))
            return sql_cmd


@db_commit
def reset_local_db_info(table_name, column_name, server_uuid):
    """
    Before collect information, clean all foregone items.
    """
    server_uuid = server_uuid
    pLogger.debug("Clean record base column [{1}] on table [{0}], with server_uuid is [{2}]".format(
        table_name, column_name, server_uuid))
    sql_like_string = "%s = '{0}'" % column_name
    pLogger.debug("sql_like_string: {}".format(sql_like_string))
    sql_like_pattern = sql_like_string.format(server_uuid)
    pLogger.debug("sql_like_pattern: {}".format(sql_like_pattern))
    sql_cmd = "DELETE FROM %s WHERE %s" % (table_name, sql_like_pattern)
    pLogger.info("{} truncate database table operation: {}".format(
        table_name, sql_cmd))
    return sql_cmd


def start_end_point(info):
    def _warper(fun):
        def warper(*args, **kwargs):
            pLogger.debug("\n" + ">" * 50 + "process project start : %s", info)
            fun(*args, **kwargs)
            pLogger.debug("\n" + "<" * 50 +
                          "process project finish : %s ", info)
        return warper
    return _warper


def pickle_load(dump_file):
    with open(dump_file, 'rb') as load_file:
        pickle_load_data = pickle.load(load_file)
        pLogger.debug("pickle_load_data is {!r}".format(pickle_load_data))
        for kv in pickle_load_data:
            pLogger.debug("pickle object is {!r},"
                          "type is {!r}".format(kv, type(kv)))
            # import2db(table, ip, port,
            # p_name, p_pid, p_exe, p_cwd,p_cmdline, p_status,
            # p_create_time, p_username,
            # server_uuid, **kwargs)
            if 'service_listens_table' in kv.keys():
                import2db(table=kv['service_listens_table'],
                          ip=kv["l_ip"],
                          port=kv['l_port'],
                          p_name=kv['name'],
                          p_pid=kv['pid'],
                          p_exe=kv['exe'],
                          p_cwd=kv['cwd'],
                          p_cmdline=kv['cmdline'],
                          p_status=kv['status'],
                          p_create_time=kv["create_time"],
                          p_username=kv["username"],
                          server_uuid=kv['server_uuid']
                          )
            elif 'service_connections_table' in kv.keys():
                import2db(table=kv['service_connections_table'],
                          ip=kv["insert_ip"],
                          port=kv['insert_port'],
                          p_name=kv['name'],
                          p_pid=kv['pid'],
                          p_exe=kv['exe'],
                          p_cwd=kv['cwd'],
                          p_cmdline=kv['cmdline'],
                          p_status=kv['status'],
                          p_create_time=kv["create_time"],
                          p_username=kv["username"],
                          server_uuid=kv['server_uuid'],
                          local_ip=kv["local_ip"],
                          )


@spend_time
@start_end_point(SCRIPT_NAME)
@script_head
def con_and_ps(picklefile):
    try:
        # Clean old data
        server_uuid = os.path.basename(picklefile)
        for table_name in [service_listens_table, service_connections_table]:
            reset_local_db_info(table_name, 'server_uuid', server_uuid)
        pickle_load(picklefile)
    except PermissionError:
        pLogger.exception("Use root user.")
        exit()


@db_close
def main():
    try:
        pickle_file = get_options()[0]
        con_and_ps(pickle_file)
    except PermissionError:
        pLogger.exception("Use root user to execution.")
        exit()


if __name__ == "__main__":
    main()
