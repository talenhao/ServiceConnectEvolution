# -*- coding: UTF-8 -*-

"""
Collect socket information.
Copyright (C) 2017-2027 Talen Hao. All Rights Reserved.
"""
# ******************************************************
__author__ = "Talen Hao(天飞)<talenhao@gmail.com>"
__create_date__ = "2017.09.05"
__last_date__ = "2017.09.30"
__version__ = __last_date__
# ******************************************************

# builtin
import re
import sys
import uuid
import getopt
import psutil
import socket
import datetime

# user module
from serconevo.model import db_connect

# for log >>
import logging
import os
from serconevo.log4p import log4p

SCRIPT_NAME = os.path.basename(__file__)
pLogger = log4p.GetLogger(SCRIPT_NAME, logging.DEBUG).get_l()
# log end <<

all_args = sys.argv[1:]
usage = '''
用法：
%s [--命令选项] [参数]

命令选项：
    --help, -h              帮助。
    --version, -V           输出版本号。
''' % sys.argv[0]

identify_line = "=*=" * 10

db_con = db_connect.DbInitConnect()
config_parser = db_con.python_config_parser
connection_table = config_parser.get("TABLE", "connections")


def get_server_uuid():
    """
    Get server uuid of which want to collected.
    """
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
        pLogger.debug("Script version: {!r}".format(__version__))
        return func(*args, **kwargs)
    return warper


# db commit
def db_commit(func):
    def warper(*args, **kwargs):
        # config_parser = db_connect.SCEConfigParser().config_parser()
        sql_cmd = func(*args, **kwargs)
        pLogger.debug("SQL_CMD is =====> {!r}  __________".format(sql_cmd))
        db_con.dictcursor.execute(sql_cmd)
        pLogger.info("==> DB operation command result: {!r}".format(
            db_con.dictcursor.rowcount))
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
        pLogger.info("Time start %s", start_time)
        func(*args, **kwargs)
        end_time = datetime.datetime.now()
        pLogger.info("Time over %s,spend %s", end_time, end_time - start_time)
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


def get_host_ip():
    ip_set = set()
    nia = psutil.net_if_addrs()
    pLogger.debug(nia)
    for i_face, addrs in nia.items():
        pLogger.debug("i_face is {}".format(i_face))
        if i_face == 'lo':
            pLogger.debug("{!r} is loop address ".format(i_face))
            continue
        else:
            for addr in addrs:
                pLogger.debug("addr is {}".format(addr))
                # here we don't need ipv6
                if str(addr.family) == 'AddressFamily.AF_INET':
                        # or str(addr.family) == 'AddressFamily.AF_INET6':
                    pLogger.debug('get ip {}'.format(addr.address))
                    ip_set.add(addr.address)
                else:
                    pLogger.debug("{!r} is not a INET address".format(addr))
    pLogger.debug("ip_set = {!r}, type {!r}".format(ip_set, type(ip_set)))
    return ip_set


def detect_socket(ip, port):
    try:
        s = socket.create_connection((ip, port))
        pLogger.debug('connection {!r}:{!r} test ok.'.format(ip, port))
        status = 'ok'
    except Exception:
        pLogger.debug("connection {!r}:{!r} has interupted".format(ip, port))
        status = 'fail'
    else:
        s.close()
    finally:
        return status


def convert_ipv6_ipv4(ipv6):
    """
    ::ffff:192.168.1.103 convert to 192.168.1.103
    """
    ip = ipv6.split(":")[-1]
    return ip


def listen_ports_collect(process, connections):
    """
    collect all listen ports.
    Here just collect tcp ESTABLISHED and udp
    tcp:
    psutil.CONN_ESTABLISHED collect
    psutil.CONN_SYN_SENT
    psutil.CONN_SYN_RECV
    psutil.CONN_FIN_WAIT1
    psutil.CONN_FIN_WAIT2
    psutil.CONN_TIME_WAIT
    psutil.CONN_CLOSE
    psutil.CONN_CLOSE_WAIT
    psutil.CONN_LAST_ACK
    psutil.CONN_LISTEN
    psutil.CONN_CLOSING
    udp&unix socket:
    psutil.CONN_NONE
    other:
    psutil.CONN_DELETE_TCB(Windows)
    psutil.CONN_IDLE(Solaris)
    psutil.CONN_BOUND(Solaris)
    """
    listen_ports_set = set()
    # First, collect all listen ip port to a set.
    pLogger.debug("First, collect all listen ip port to a set.")
    for connection in connections:
        # tcp
        if connection.status == psutil.CONN_LISTEN:
                # or (connection.status == psutil.CONN_NONE and not connection.raddr)\
            pLogger.debug("[{!r}] CONN_LISTEN connection is {!r}".format(
                process.pid, connection))
            listen_ports_set.add(
                connection.laddr[1])
            pLogger.debug("[{}] connection.laddr is {!r}".format(
                process.pid, connection.laddr))
        # none LISTENS process
        # else:
        #     pLogger.debug(
        #         "{!r} is not LISTEN connection!".format(connection))
    pLogger.debug('listen_ports_set : {}'.format(listen_ports_set))
    pLogger.debug("End, collect all listen ip port to a set.")
    return listen_ports_set


def ps_collect():
    # get bind ip for this server.
    server_ip = get_host_ip()
    # listen_ip_list = server_ip
    server_uuid = get_server_uuid()
    listen_ports = []
    # 直接使用process_iter()迭代实例化每个进程.
    try:
        for process in psutil.process_iter():
            pLogger.debug("{}\n\nPID [{}] begin to process.".format(
                identify_line,
                process.pid)
            )
            # detect process is running.
            if process.is_running():
                # salt-minion with different pid but use the same socket.
                process_listen_port_processed = set()
                pid = process.pid
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
                            username = process.username()
                            # collect all listen ports with this process.
                            process_listen_port = listen_ports_collect(process, connections)

                            # Second, collect all connections tag a flag.
                            pLogger.debug('Second, collect all connections tag a flag.____________________')
                            for connection in connections:
                                pLogger.debug("Pid [{!r}] has connection: {!r}.\n".format(
                                    pid,
                                    connection)
                                )
                                laddr, raddr = connection.laddr, connection.raddr
                                pLogger.debug("laddr, raddr is {!r}, {!r}".format(laddr, raddr))
                                # ip to ipv4
                                l_ip, l_port = laddr
                                l_ip = convert_ipv6_ipv4(l_ip)

                                if connection.status == psutil.CONN_LISTEN:
                                    pLogger.debug("*************************"
                                                  "process_listen_port is : {} ,"
                                                  "listen_ports is {!r},"
                                                  "process_listen_port_processed: {} ====>".format(
                                                      process_listen_port,
                                                      set(listen_ports),
                                                      process_listen_port_processed)
                                                  )

                                    # exclude other process have the same listening port.
                                    if connection.laddr[1] in listen_ports:
                                        pLogger.debug("Duplicate listening port, drop.")
                                        continue
                                    # exclude one process listening on ipv4 and ipv6
                                    elif connection.laddr[1] in process_listen_port_processed:
                                        pLogger.debug("Duplicate ipv6 or ipv4 listen port, drop it."
                                                      " process_listen_port_processed is {!r}".format(
                                                          process_listen_port_processed)
                                                      )
                                        continue
                                    else:
                                        flag = 0
                                        r_ip_set = set()
                                        r_ip = None
                                        r_ip_set.add(r_ip)
                                        r_port = None
                                        l_ip_set = server_ip
                                        process_listen_port_processed.add(l_port)
                                        pLogger.debug("append listen port {} to process_listen_port_processed".format(
                                            l_port)
                                        )
                                elif connection.status == psutil.CONN_ESTABLISHED:
                                    laddr_connected = detect_socket(connection.raddr[0], connection.raddr[1])
                                    if laddr_connected == "fail":
                                        # pLogger.debug("ESTABLISHED {!r} is interupted.".format(connection.raddr))
                                        continue
                                    elif laddr_connected == 'ok':
                                        # pLogger.debug("ESTABLISHED {!r} is connected.".format(connection.raddr))
                                        # connection direction, 0 reverse, 1 positive
                                        if connection.laddr[1] in process_listen_port:
                                            flag = 0
                                        else:
                                            flag = 1
                                        pLogger.debug("Pid [{!r}] has flag: {!r}".format(
                                            pid,
                                            flag)
                                        )
                                        r_ip, r_port = raddr
                                        r_ip = convert_ipv6_ipv4(r_ip)
                                        if r_ip in ['127.0.0.1', '1']:
                                            pLogger.debug("connect to {}, lo will be replaced with server_ip".format(
                                                raddr)
                                            )
                                            r_ip_set = server_ip
                                        else:
                                            r_ip_set = set()
                                            r_ip_set.add(r_ip)
                                        l_ip_set = set()
                                        l_ip_set.add(l_ip)
                                else:
                                    pLogger.debug("connection {!r} with status {!r} don't wanted collect, drop!".format(
                                        connection, connection.status))
                                    continue
                                pLogger.debug("l_ip, l_port, r_ip, r_port is {!r}, {!r}, {!r}, {!r}, "
                                              "l_ip_set is {!r}, r_ip_set is {!r}".format(
                                                  l_ip, l_port, r_ip, r_port, l_ip_set, r_ip_set)
                                              )
                                if isinstance(l_ip_set, set) and isinstance(r_ip_set, set):
                                    for l_ip_address in l_ip_set:
                                        for r_ip_address in r_ip_set:
                                            import2db(connection_table, l_ip_address, l_port, r_ip, r_port,
                                                      name, pid, exe, cwd, cmdline, status, create_time, username,
                                                      server_uuid, local_ip=server_ip, flag=flag
                                                      )
                            if process_listen_port:
                                listen_ports.extend(list(process_listen_port))
                                listen_ports = list(set(listen_ports))
                        else:
                            pLogger.debug("{} has no connections.".format(pid))
                    except psutil.NoSuchProcess as e:
                        pLogger.warn(e)
            else:
                pLogger.debug(
                    "process {} is already not exist!".format(process.pid))
            pLogger.debug("Porcesses [{1}] end to process. {0}".format(
                identify_line, process.pid))
    except psutil.AccessDenied:
        pLogger.exception("用户权限不足.")
        sys.exit()


def create_list_to_str(item, num):
    format_str = ",".join([item for i in range(num)])
    return format_str


def process_before_insert_db(string):
    """
    process cmdline @,#... because it will raise error when insert mysql
    """
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
    except Exception:
        pLogger.error("There has some error when convert {}.".format(string))
        exit()


@db_commit
def import2db(table, l_ip, l_port, r_ip, r_port, p_name, p_pid, p_exe, p_cwd, p_cmdline,
              p_status, p_create_time, p_username,
              server_uuid, local_ip, flag
              ):
    process_before_insert_db(p_cmdline)
    columns_list_process = ["l_ip", "l_port", "r_ip", "r_port", "p_name", "p_pid", "p_exe", "p_cwd", "p_cmdline",
                            "p_status", "p_create_time", "p_username", "server_uuid", "local_ip", "flag"]
    values_list = [l_ip, l_port, r_ip, r_port, p_name, p_pid, p_exe,
                   p_cwd, p_cmdline, p_status, p_create_time, p_username,
                   server_uuid, local_ip, flag]
    # pLogger.debug("columns_list_process is {}, values_list is {}".format(
    #     columns_list_process, values_list))

    # 2 SQL create
    columns_str = ','.join(
        ['{1' + str([i]) + '}' for i in range(len(columns_list_process))])
    values_str = ",".join(
        ['"{2' + str([i]) + '}"' for i in range(len(values_list))])
    # pLogger.debug("columns_str is : {!r}, values_str is : {!r} .".format(
    #     columns_str, values_str))
    sql_format_str = 'INSERT ignore INTO {0} (' + \
        columns_str + ') VALUES (' + values_str + ')'
    # pLogger.debug("sql_format_str is : {!r}".format(sql_format_str))
    sql_cmd = sql_format_str.format(
        table, columns_list_process, values_list)
    # pLogger.debug("_sql is : {!r}".format(sql_cmd))
    # pLogger.debug("{} insert database operation command: {}".format(p_exe, sql_cmd))
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
    pLogger.debug("{} truncate database table operation: {}".format(
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


@spend_time
@start_end_point(SCRIPT_NAME)
@script_head
def con_and_ps():
    try:
        # Clean old data
        reset_local_db_info(connection_table, 'server_uuid')
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
