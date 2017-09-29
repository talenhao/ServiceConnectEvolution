# -*- coding: UTF-8 -*-

"""
Collect socket information.
Copyright (C) 2017-2027 Talen Hao. All Rights Reserved.
"""
# todo: process p_cwd

# builtin
import re
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
__last_date__ = "2017.09.30"
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

identify_line = "=*=" * 20

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
    for i_face in nia.values():
        pLogger.debug("i_face is {}".format(i_face))
        for addr in i_face:
            pLogger.debug("addr is {}".format(addr))
            if addr.address != '127.0.0.1' and addr.address != '::1':
                if str(addr.family) == 'AddressFamily.AF_INET' or str(addr.family) == 'AddressFamily.AF_INET6':
                    pLogger.debug('get ip {}'.format(addr.address))
                    ip_set.add(addr.address)
                else:
                    pLogger.warn("{!r} is not a INET address".format(addr))
            else:
                pLogger.warn("{!r} is loop address ".format(addr))
    pLogger.debug("ip_set = {!r}".format(ip_set))
    return ip_set


def ps_collect():
    # get bind ips for this server.
    server_ip = get_server_ip()
    listen_ip_list = server_ip
    server_uuid = get_server_uuid()
    # 直接使用process_iter()迭代实例化每个进程.
    try:
        for process in psutil.process_iter():
            pLogger.debug("\n{}\nPID [{}] begin to process.".format(
                identify_line,
                process.pid)
            )
            # 判断进程是否还在运行.
            if process.is_running():
                pid = process.pid
                process_listen_port = set()
                process_connection_ip_port = set()
                # 一次性抓取运行快照
                with process.oneshot():
                    # 连接信息
                    try:
                        connections = process.connections(kind='inet')
                        if connections:
                            # 只处理有连接的进程
                            name = process.name()
                            exe = process.exe()
                            cwd = process.cwd()
                            cmdline = process.cmdline()

                            status = process.status()
                            # 转换成utc写入数据库
                            create_time = process.create_time()
                            create_time = datetime.datetime.utcfromtimestamp(
                                create_time) + datetime.timedelta(hours=8)
                            create_time = str(create_time)
                            pLogger.debug(
                                "{!r} create_time is {!r}".format(pid, create_time))
                            # num_ctx_switches = process.num_ctx_switches()
                            username = process.username()
                            # memory_full_info = process.memory_full_info()

                            # LISTENS
                            for connection in connections:
                                # 监听连接单独处理
                                if connection.status == psutil.CONN_LISTEN \
                                        or (connection.status == psutil.CONN_NONE and not connection.raddr):
                                    pLogger.debug("[{!r}] CONN_LISTEN connection is {!r}".format(
                                        process.pid, connection))
                                    process_listen_port.add(
                                        connection.laddr[1])
                                    pLogger.debug("[{}] connection.laddr is {!r}".format(
                                        process.pid, connection.laddr))
                                # none LISTENS process
                                else:
                                    pLogger.debug(
                                        "{!r} is not LISTEN connection!".format(connection))
                            # take out from set.
                            if process_listen_port:
                                pLogger.debug("{!r} process_listen_port is {!r}".format(
                                    pid, process_listen_port))
                                pLogger.info(
                                    "{!r} insert listen to DB.".format(pid))
                                # 如果连接地址为127.0.0.1,替换成非loop地址
                                for l_port in process_listen_port:
                                    for l_ip in listen_ip_list:
                                        import2db(service_listens_table, l_ip, l_port, name, pid, exe, cwd,
                                                  cmdline, status, create_time, username, server_uuid)
                            else:
                                pLogger.debug(
                                    "Process {} with pid {} has no listen ports!".format(process, pid))
                            pLogger.info("process_listen_port is : {}".format(
                                process_listen_port))

                            # CONNECTIONS
                            for connection in connections:
                                # 从连接池中排除连接到自身监听的端口的链接
                                if connection.status != psutil.CONN_LISTEN \
                                        and connection.laddr[1] not in process_listen_port:
                                        # and connection.status !=
                                        # psutil.CONN_NONE \
                                    flag = 1
                                    pLogger.debug("[{!r}] connection {!r} has connection.raddr is {!r}".format(
                                        pid,
                                        connection,
                                        connection.raddr))
                                    process_connection_ip_port.add((connection.raddr, flag))
                                elif connection.status != psutil.CONN_LISTEN \
                                        and connection.laddr[1] in process_listen_port and connection.raddr:
                                    flag = 0
                                    pLogger.debug("{!r} connect {!r}, from connection.raddr is {!r}".format(
                                        connection,
                                        pid,
                                        connection.raddr))
                                    process_connection_ip_port.add((connection.raddr, flag))
                                else:
                                    pLogger.debug(
                                        "{!r} is not our collect connection!".format(connection))

                            if process_connection_ip_port:
                                db_insert_ip_list = []
                                pLogger.debug("{!r} process_connection_ip_port is"
                                              " {!r}".format(
                                                  pid,
                                                  process_connection_ip_port)
                                              )
                                for connection_raddr in process_connection_ip_port:
                                    con, flag = connection_raddr
                                    c_ip, c_port = con
                                    pLogger.debug(
                                        "Before convert c_ip is {!r}".format(c_ip))
                                    # ip to ipv4
                                    c_ip = c_ip.split(":")[-1]
                                    pLogger.debug(
                                        'c_ip, c_port is {} : {}'.format(c_ip, c_port))
                                    # 如果是连接127.0.0.1或::1,替换成本机IP
                                    if c_ip == '1' or c_ip == '127.0.0.1':
                                        pLogger.debug(
                                            "c_ip {!r} is loop, replace local real ip.".format(c_ip))
                                        for c_ip_local_to_real in listen_ip_list:
                                            pLogger.info("{} insert connection {!r} to DB insert list with flag {!r}"
                                                         .format(pid, c_ip_local_to_real, flag))
                                            db_insert_ip_list.append(
                                                (c_ip_local_to_real, c_port, flag))
                                    else:
                                        pLogger.debug(
                                            "c_ip {} insert into db insert list with flag {!r}".format(c_ip, flag))
                                        db_insert_ip_list.append(
                                            (c_ip, c_port, flag))

                                for insert in db_insert_ip_list:
                                    insert_ip, insert_port, flag = insert
                                    import2db(service_connections_table, insert_ip, insert_port, name, pid, exe,
                                              cwd, cmdline, status, create_time, username,
                                              server_uuid, local_ip=server_ip, flag=flag)
                            else:
                                pLogger.debug(
                                    "process_connection_ip_port is empty!")
                        else:
                            pLogger.debug("{} has no connections.".format(pid))
                    except psutil.NoSuchProcess as e:
                        pLogger.warn(e)

            else:
                pLogger.debug(
                    "process {} is already not exist!".format(process.pid))
            pLogger.debug("\nPorcesses [{1}] end to process.\n{0}".format(
                identify_line, process.pid))
    except psutil.AccessDenied:
        pLogger.exception("用户权限不足.")
        sys.exit()


def create_list_to_str(item, num):
    format_str = ",".join([item for i in range(num)])
    return format_str


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
    except:
        pLogger.error("There has some error when convert {}.".format(string))
        exit()


@db_commit
def import2db(table, ip, port, p_name, p_pid, p_exe, p_cwd, p_cmdline, p_status, p_create_time, p_username,
              server_uuid, **kwargs):
    pLogger.debug("import2db kwargs is {!r}".format(kwargs))
    process_before_insert_db(p_cmdline)
    # 1 column_values create
    ip_column = ""
    port_column = ""
    columns_num = 0
    columns_list_process = ["p_name", "p_pid", "p_exe", "p_cwd", "p_cmdline",
                            "p_status", "p_create_time", "p_username", "server_uuid"]
    values_list = [ip, port, p_name, p_pid, p_exe,
                   p_cwd, p_cmdline, p_status, p_create_time, p_username,
                   server_uuid]
    pLogger.debug("columns_list_process is {}, values_list is {}".format(
        columns_list_process, values_list))
    try:
        if table == service_listens_table:
            ip_column = "l_ip"
            port_column = "l_port"
            columns_num = 11
            pLogger.debug("Table is {}, column_num is {}".format(
                service_listens_table, columns_num))
            # format_str = create_list_to_str('{!r}', columns_num)
            # format_str_value = create_list_to_str('"{!r}"', columns_num)
        elif table == service_connections_table and kwargs['local_ip']:
            ip_column = "c_ip"
            port_column = "c_port"
            columns_num = 13
            pLogger.debug("Table is {}, column_num is {}, append column.".format(
                service_listens_table, columns_num))
            columns_list_process.append('local_ip')
            columns_list_process.append('flag')
            values_list.append(kwargs['local_ip'])
            values_list.append(kwargs['flag'])

    except ValueError:
        pLogger.exception(
            "Please check the table name argument {}.".format(table))
        exit()
    else:
        if ip_column and port_column:
            columns_list_t_i_p = [ip_column, port_column]
            columns_list_t_i_p.extend(columns_list_process)
            pLogger.debug(
                "columns_list_t_i_p is : {!r}, type {!r}".format(columns_list_t_i_p, type(columns_list_t_i_p)))
            # 2 SQL create
            columns_str = ','.join(
                ['{1' + str([i]) + '}' for i in range(columns_num)])
            values_str = ",".join(
                ['"{2' + str([i]) + '}"' for i in range(columns_num)])
            pLogger.debug("columns_str is : {!r}, values_str is : {!r} .".format(
                columns_str, values_str))
            sql_format_str = 'INSERT ignore INTO {0} (' + \
                columns_str + ') VALUES (' + values_str + ')'
            pLogger.debug("sql_format_str is : {!r}".format(sql_format_str))
            sql_cmd = sql_format_str.format(
                table, columns_list_t_i_p, values_list)
            pLogger.debug("_sql is : {!r}".format(sql_cmd))
            pLogger.debug(
                "{} insert database operation command: {}".format(p_exe, sql_cmd))
            return sql_cmd


@db_commit
def reset_local_db_info(table_name, column_name):
    """
    在每台服务器执行全收集的时候，先清除旧的数据库信息;
    """
    server_uuid = get_server_uuid()
    pLogger.debug("Clean record base column [{1}] on table [{0}].".format(
        table_name, column_name))
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
