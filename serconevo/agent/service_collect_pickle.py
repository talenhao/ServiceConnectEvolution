# -*- coding: UTF-8 -*-

"""
Collect socket information.
Copyright (C) 2017-2027 Talen Hao. All Rights Reserved.
"""
# todo: process p_cwd

# builtin
import uuid
import sys
import getopt
import datetime
import psutil
import pickle

# user module
from serconevo.model import db_connect_for_pickle

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

identify_line = "=*=" * 20

db_con = db_connect_for_pickle.DbInitConnect()
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
    pickle_list = []
    server_ip = get_server_ip()
    listen_ip_list = server_ip
    server_uuid = get_server_uuid()
    # 直接使用process_iter()迭代实例化每个进程.
    try:
        for process in psutil.process_iter():
            pLogger.debug("\n{}\nPID [{}] begin to process.".format(identify_line, process.pid))
            # 判断进程是否还在运行.
            if process.is_running():
                pid = process.pid
                # 一次性抓取运行快照
                process_listen_port = set()
                process_connection_ip_port = set()
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
                            create_time = datetime.datetime.utcfromtimestamp(create_time) + datetime.timedelta(hours=8)
                            create_time = str(create_time)
                            pLogger.debug("{!r} create_time is {!r}".format(pid, create_time))
                            # num_ctx_switches = process.num_ctx_switches()
                            username = process.username()
                            # memory_full_info = process.memory_full_info()

                            # LISTENS
                            for connection in connections:
                                # 监听连接单独处理
                                if connection.status == psutil.CONN_LISTEN \
                                        or (connection.status == psutil.CONN_NONE and not connection.raddr):
                                    pLogger.debug("[{!r}] CONN_LISTEN connection is {!r}".format(process.pid, connection))
                                    process_listen_port.add(connection.laddr[1])
                                    pLogger.debug("[{}] connection.laddr is {!r}".format(process.pid, connection.laddr))
                                # none LISTENS process
                                else:
                                    pLogger.debug("{!r} is not LISTEN connection!".format(connection))
                            # take out from set.
                            if process_listen_port:
                                pLogger.debug("{!r} process_listen_port is {!r}".format(pid, process_listen_port))
                                pLogger.info("{!r} insert listen to DB.".format(pid))
                                # 如果连接地址为127.0.0.1,替换成非loop地址
                                for l_port in process_listen_port:
                                    for l_ip in listen_ip_list:
                                        # import2db(service_listens_table, l_ip, l_port, name, pid, exe, cwd,
                                        #           cmdline, status, create_time, username, server_uuid)
                                        pickle_list.append({"service_listens_table": service_listens_table,
                                                               "l_ip": l_ip,
                                                               "l_port": l_port,
                                                               "name": name,
                                                               "pid": pid,
                                                               "exe": exe,
                                                               "cwd": cwd,
                                                               "cmdline": cmdline,
                                                               "status": status,
                                                               "create_time": create_time,
                                                               "username": username,
                                                               "server_uuid": server_uuid})
                            else:
                                pLogger.debug("Process {} with pid {} has no listen ports!".format(process, pid))
                            pLogger.info("process_listen_port is : {}".format(process_listen_port))
                            # CONNECTIONS
                            for connection in connections:
                                # 从连接池中排除连接到自身监听的端口的链接
                                if connection.status != psutil.CONN_LISTEN \
                                        and connection.laddr[1] not in process_listen_port:
                                        # and connection.status != psutil.CONN_NONE \
                                    pLogger.debug("[{!r}] connection {!r} has connection.raddr is {!r}".format(
                                            pid,
                                            connection,
                                            connection.raddr))
                                    process_connection_ip_port.add(connection.raddr)
                                else:
                                    pLogger.debug("{!r} is not our collect connection!".format(connection))

                            if process_connection_ip_port:
                                db_insert_ip_list = []
                                pLogger.debug("{!r} process_connection_ip_port is {!r}".format(pid,
                                                                                               process_connection_ip_port))
                                for connection_raddr in process_connection_ip_port:
                                    c_ip, c_port = connection_raddr
                                    pLogger.debug("Before convert c_ip is {!r}".format(c_ip))
                                    # ip to ipv4
                                    c_ip = c_ip.split(":")[-1]
                                    pLogger.debug('c_ip, c_port is {} : {}'.format(c_ip, c_port))
                                    # 如果是连接127.0.0.1或::1,替换成本机IP
                                    if c_ip == '1' or c_ip == '127.0.0.1':
                                        pLogger.debug("c_ip {!r} is loop, replace local real ip.".format(c_ip))
                                        for c_ip_local_to_real in listen_ip_list:
                                            pLogger.info("{} insert connection {!r} to DB insert list."
                                                         .format(pid, c_ip_local_to_real))
                                            db_insert_ip_list.append((c_ip_local_to_real, c_port))
                                    else:
                                        pLogger.debug("c_ip {} insert into db insert list.".format(c_ip))
                                        db_insert_ip_list.append((c_ip, c_port))

                                for insert in db_insert_ip_list:
                                    insert_ip, insert_port = insert
                                    # import2db(service_connections_table, insert_ip, insert_port, name, pid, exe,
                                    #           cwd, cmdline, status, create_time, username,
                                    #           server_uuid, local_ip=server_ip)
                                    pickle_list.append({"service_connections_table": service_connections_table,
                                                               "insert_ip": insert_ip,
                                                               "insert_port": insert_port,
                                                               "name": name,
                                                               "pid": pid,
                                                               "exe": exe,
                                                               "cwd": cwd,
                                                               "cmdline": cmdline,
                                                               "status": status,
                                                               "create_time": create_time,
                                                               "username": username,
                                                               "server_uuid": server_uuid,
                                                               "local_ip": server_ip})
                            else:
                                pLogger.debug("process_connection_ip_port is empty!")
                        else:
                            pLogger.debug("{} has no connections.".format(pid))
                    except psutil.NoSuchProcess as e:
                        pLogger.warn(e)

            else:
                pLogger.debug("process {} is already not exist!".format(process.pid))
            pLogger.debug("\nPorcesses [{1}] end to process.\n{0}".format(identify_line, process.pid))
    except psutil.AccessDenied:
        pLogger.exception("用户权限不足.")
        sys.exit()
    with open(server_uuid, 'wb') as dump_file:
        pickle.dump(pickle_list, dump_file, True)


def create_list_to_str(item, num):
    format_str = ",".join([item for i in range(num)])
    return format_str


def start_end_point(info):
    def _warper(fun):
        def warper(*args, **kwargs):
            pLogger.debug("\n" + ">" * 50 + "process project start : %s", info)
            fun(*args, **kwargs)
            pLogger.debug("\n" + "<" * 50 + "process project finish : %s ", info)
        return warper
    return _warper


@spend_time
@start_end_point(SCRIPT_NAME)
@script_head
def con_and_ps():
    try:
        ps_collect()
    except PermissionError:
        pLogger.exception("Use root user.")
        exit()


def main():
    get_options()
    try:
        con_and_ps()
    except PermissionError:
        pLogger.exception("Use root user to execution.")
        exit()


if __name__ == "__main__":
    main()
