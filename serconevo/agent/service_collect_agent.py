# -*- coding: UTF-8 -*-

"""
Collect socket information.
Copyright (C) 2017-2027 Talen Hao. All Rights Reserved.
"""

# builtin
import uuid
import sys
import getopt
import datetime
import psutil

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
%s [--命令选项] [参数]

命令选项：
    --help, -h              帮助。
    --version, -V           输出版本号。
''' % sys.argv[0]

identify_line = "=*=" * 30

db_con = db_connect.DbInitConnect()
config_parser = db_con.python_config_parser
service_listens_table = config_parser.get("TABLE", "listen_table")
service_connections_table = config_parser.get("TABLE", "connection_table")


def get_server_uuid():
    # server_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, __author__))
    # 使用'dmidecode'命令生成（不足：需要使用root权限）。后来发现uuid模块的getnode生成的uuid竟然跟'dmidecode'是一样的。
    # 参考http://stackoverflow.com/questions/2461141/get-a-unique-computer-id-in-python-on-windows-and-linux
    server_uuid = str(uuid.UUID(int=uuid.getnode()))
    pLogger.info("server_uuid is: %s", server_uuid)
    return server_uuid


# python版本判断，帮助等装饰器。
def script_head(func):
    def warper(*args, **kwargs):
        if sys.version_info < (3, 4):
            pLogger.warning('友情提示：当前系统版本低于3.4，请升级python版本。')
            raise RuntimeError('At least Python 3.4 is required')
        pLogger.info("Script version: {!r}".format(__version__))
        return func(*args, **kwargs)
    return warper


# db commit
def db_commit(func):
    def warper(*args, **kwargs):
        # config_parser = db_connect.SCEConfigParser().config_parser()
        sql_cmd = func(*args, **kwargs)
        pLogger.debug("SQL_CMD is =====> {!r}  __________".format(sql_cmd))
        db_con.cursor.execute(sql_cmd)
        pLogger.info("=====> DB operation command result: {!r}".format(db_con.cursor.rowcount))
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


def get_options():
    if all_args:
        pLogger.debug("Command arguments: {!r}".format(str(all_args)))
    # else:
        # pLogger.error(usage)
        # sys.exit()
    try:
        opts, args = getopt.getopt(all_args, "hV", ["help", "version"])
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


def get_server_ip():
    ip_set = set()
    nia = psutil.net_if_addrs()
    pLogger.debug(nia)
    for v in nia.values():
        if v[0].address != '127.0.0.1':
            pLogger.debug('get ip {}'.format(v[0].address))
            ip_set.add(v[0].address)
    pLogger.debug("ip_set = {!r}".format(ip_set))
    return ip_set


def ps_collect():
    server_ip = get_server_ip()
    server_uuid = get_server_uuid()
    # 直接使用process_iter()迭代实例化每个进程.
    try:
        for process in psutil.process_iter():
            pLogger.debug("{}\nPorcesses [{}] begin to process.".format(identify_line, process.pid))
            # 判断进程是否还在运行.
            if process.is_running():
                # 一次性抓取运行快照
                process_listen_port = set()
                process_connection_ip_port = set()
                with process.oneshot():
                    # 连接信息
                    connections = process.connections()
                    if connections:
                        # 只处理有连接的进程
                        name = process.name()
                        pid = process.pid
                        exe = process.exe()
                        cwd = process.cwd()
                        cmdline = process.cmdline()
                        status = process.status()
                        # 转换成utc写入数据库
                        create_time = process.create_time()
                        create_time = datetime.datetime.utcfromtimestamp(create_time) + datetime.timedelta(hours=8)
                        create_time = str(create_time)
                        pLogger.debug("{!r} create_time is {!r}".format(pid, create_time))
                        # num_ctx_switches = process.num_ctx_switches()
                        username = process.username()
                        # memory_full_info = process.memory_full_info()
                
                        for connection in connections:
                            # 监听连接单独处理
                            if connection.status == psutil.CONN_LISTEN:
                                # 如果连接地址为127.0.0.1,替换成非loop地址
                                process_listen_port.add(connection.laddr[1])
                                # none LISTENS process
                
                        for connection in connections:
                            if connection.status != psutil.CONN_LISTEN and \
                                            connection.status != psutil.CONN_NONE and \
                                            connection.laddr[1] not in process_listen_port:
                                pLogger.debug("connection {!r} has connection.raddr is {!r}".format(connection,
                                                                                                    connection.raddr))
                                process_connection_ip_port.add(connection.raddr)
                
                        # take out from set.
                        if process_listen_port:
                            pLogger.debug("{!r} process_listen_port is {!r}".format(pid, process_listen_port))
                            pLogger.info("{} insert listen to DB.".format(pid))
                            import2db(service_listens_table, server_ip, process_listen_port, name, pid, exe, cwd,
                                      cmdline, status, create_time, username, server_uuid)
                        else:
                            pLogger.warn("Process {} with pid {} has no listen ports!".format(process, pid))
                        # 从laddr中排除自身监听的端口
                        if process_connection_ip_port:
                            pLogger.debug("{!r} process_connection_ip_port is {!r}".format(pid,
                                                                                           process_connection_ip_port))
                            for connection_raddr in process_connection_ip_port:
                                c_ip, c_port = connection_raddr
                                pLogger.info("{} insert connection to DB.".format(pid))
                                import2db(service_connections_table, c_ip, c_port, name, pid, exe, cwd,
                                          cmdline, status, create_time, username, server_uuid, local_ip=server_ip)
                        else:
                            pLogger.warn("{} has no connections.".format(pid))
    
            else:
                pLogger.warn("process {} is already not exist!".format(process.pid))
    except psutil.AccessDenied:
        pLogger.exception("用户权限不足.")
        sys.exit()


def create_list_to_str(item, num):
    format_str = ",".join([item for i in range(num)])
    return format_str
    
    
@db_commit
def import2db(table, ip, port, p_name, p_pid, p_exe, p_cwd, p_cmdline, p_status, p_create_time, p_username,
              server_uuid, **kwargs):
    pLogger.debug(kwargs)
    # 1 column_values create
    ip_column = ""
    port_column = ""
    columns_num = 0
    columns_list_process = ["p_name", "p_pid", "p_exe", "p_cwd", "p_cmdline",
                            "p_status", "p_create_time", "p_username", "server_uuid"]
    values_list = [ip, port, p_name, p_pid, p_exe,
                   p_cwd, p_cmdline, p_status, p_create_time, p_username,
                   server_uuid]
    pLogger.debug("columns_list_process is {}, values_list is {}".format(columns_list_process, values_list))
    try:
        if table == service_listens_table:
            ip_column = "l_ip"
            port_column = "l_port"
            columns_num = 11
            # format_str = create_list_to_str('{!r}', columns_num)
            # format_str_value = create_list_to_str('"{!r}"', columns_num)
        elif table == service_connections_table and kwargs['local_ip']:
            ip_column = "c_ip"
            port_column = "c_port"
            columns_num = 12
            columns_list_process.append('local_ip')
            values_list.append(kwargs['local_ip'])
    except ValueError:
        pLogger.exception("Please check the table name argument {}.".format(table))
        exit()
    else:
        if ip_column and port_column:
            columns_list_t_i_p = [ip_column, port_column]
            columns_list_t_i_p.extend(columns_list_process)
            pLogger.debug(
                "columns_list_t_i_p is : {!r}, type {!r}".format(columns_list_t_i_p, type(columns_list_t_i_p)))
            # 2 SQL create
            columns_str = ','.join(['{1' + str([i]) + '}' for i in range(columns_num)])
            values_str = ",".join(['"{2' + str([i]) + '}"' for i in range(columns_num)])
            pLogger.debug("columns_str is : {!r}, values_str is : {!r} .".format(columns_str, values_str))
            sql_format_str = 'INSERT ignore INTO {0} (' + columns_str + ') VALUES (' + values_str + ')'
            pLogger.debug("sql_format_str is : {!r}".format(sql_format_str))
            sql_cmd = sql_format_str.format(table, columns_list_t_i_p, values_list)
            pLogger.debug("_sql is : {!r}".format(sql_cmd))
            pLogger.debug("{} insert database operation command: {}".format(p_exe, sql_cmd))
            return sql_cmd


@db_commit
def reset_local_db_info(table_name, column_name):
    """
    在每台服务器执行全收集的时候，先清除旧的数据库信息;
    """
    server_uuid = get_server_uuid()
    pLogger.debug("Clean record base column [{1}] on table [{0}].".format(table_name, column_name))
    sql_like_string = "%s = '{0}'" % column_name
    pLogger.debug("sql_like_string: {}".format(sql_like_string))
    sql_like_pattern = sql_like_string.format(server_uuid)
    pLogger.debug("sql_like_pattern: {}".format(sql_like_pattern))
    sql_cmd = "DELETE FROM %s WHERE %s" % (table_name, sql_like_pattern)
    pLogger.info("{} truncate database table operation: {}".format(table_name, sql_cmd))
    return sql_cmd


def start_end_point(info):
    def _warper(fun):
        def warper(*args, **kwargs):
            pLogger.debug("\n" + ">" * 50 + "process project start : %s", info)
            fun(*args, **kwargs)
            pLogger.debug("\n" + "<" * 50 + "process project finish : %s ", info)
        return warper
    return _warper


# 老式多线程方法，放弃。
# def _collect_worker():
#     thread_list = []
#     app_listen_instance = AppListen()
#     app_listen_con_db_project_list = app_listen_instance.project_list()
#     loop = len(app_listen_con_db_project_list)
#     for project_item in app_listen_con_db_project_list:  # project name
#         thread_instance = threading.Thread(target=do_collect, args=(project_item,))
#         thread_list.append(thread_instance)
#     # 启动线程
#     for instance_item in range(loop):
#         thread_list[instance_item].start()
#     # 等待所有线程结束
#     for instance_item in range(loop):
#         thread_list[instance_item].join()
#     pLogger.info("All collect thread finished.")
# 
#
# class CollectWorker(threading.Thread):
#     def __init__(self, queue):
#         threading.Thread.__init__(self)
#         self.queue = queue
# 
#     def run(self):
#         while True:
#             # 从队列中获取项目名
#             project_item = self.queue.get()
#             do_collect(project_item)
#             self.queue.task_done()
#
#
# def main():
#     app_listen_instance = AppListen()
#     app_listen_con_db_project_list = app_listen_instance.project_list()
#     for worker in range(cpu_count()/6):
#         worker = CollectWorker(Queue)
#         worker.setDaemon(True)
#         worker.start()
#     for project_item in app_listen_con_db_project_list:
#         Queue.put(project_item)
#     Queue.join()
#     pLogger.info("All worker finished.")


@spend_time
@start_end_point(SCRIPT_NAME)
@script_head
def con_and_ps():
    try:
        # Clean old data
        for table_name in [service_listens_table, service_connections_table]:
            reset_local_db_info(table_name, 'server_uuid')
        # Collect new data
        ps_collect()
    except PermissionError:
        pLogger.exception("Use root user.")
        exit()


@db_close
def main():
    get_options()
    try:
        con_and_ps()
    except PermissionError:
        pLogger.exception("Use root user to execution.")
        exit()
    
if __name__ == "__main__":
    main()
