# -*- coding: UTF-8 -*-
"""
# ******************************************************
# * author: "Talen Hao(天飞)<talenhao@gmail.com>"      *
# ******************************************************
"""
# todo ok 127.0.0.1 connect 127.0.0.1
# todo ok drop ip map
# todo ok process None:None raddr

import traceback
import re
# import pdb
# import time

# import user modles
from serconevo.agent import script_head
from serconevo.agent import db_close
from serconevo.agent import spend_time
from serconevo.agent import start_end_point
from serconevo import identify_line
from serconevo.agent import connection_table
from serconevo.agent import db_con
from serconevo.netgraph.drawgraph import netgraph_path
from serconevo.netgraph.drawgraph import load_draw
from serconevo.netgraph.drawgraph import pickle_to_file

# for log >>
import logging
import os
from serconevo.log4p import log4p
SCRIPT_NAME = os.path.basename(__file__)
# log end <<
pLogger = log4p.GetLogger(SCRIPT_NAME, logging.DEBUG).get_l()

fetch_list = []


def match_sort(project, string):
    """
    The first 5 fields are intercepted.
    """
    re_compile = re.compile(r'=(/[-\w]+){1,5}\b')
    re_findall = re_compile.search(string)
    pLogger.debug("re_findall: {!r}".format(re_findall))
    try:
        find_one = re_findall.group(0)
    except AttributeError:
        pLogger.debug("{} has no re compile!! It is : \n{}".format(project, string))
        return string
    else:
        pLogger.debug("find_one is : {!r}".format(find_one))
        return find_one


def db_fetchall(sql_cmd, fetch=None):
    """
    execute sql_cmd, if no set fetch arg, default return 10 results;
    if set fetch arg, it can be set 'one' or 'all'.
    :param sql_cmd:
    :param fetch:
    :return: result
    """
    pLogger.debug("SQL_CMD is ==> {!r}".format(sql_cmd))
    # pLogger.info("=====> DB operation command result: {!r}".format(db_con.cursor.rowcount))
    # pdb.set_trace()
    if fetch == 'one':
        db_con.dictcursor.execute(sql_cmd)
        result = db_con.dictcursor.fetchone()
    elif fetch == "all":
        db_con.ssdictcursor.execute(sql_cmd)
        result = db_con.ssdictcursor.fetchall()
    else:
        pLogger.error("fetch argument required.")
        result = None
    return result


def node_match(name, cwd=None, cmdline=None):
    """
    process P_name, cmdline maybe any string list;
    you cat assign some node name use p_name or use a short identify.
    :param name:
    :param cwd:
    :param cmdline:
    :return:
    """
    drop_list = ['ssh', 'sshd', 'whois', 'salt-minion', 'salt-master', 'collect.py']
#    from_drop_list = ['ssh', 'sshd', 'whois']
#    target_drop_list = ['sshd']
#    if flag == 'f':
#        drop_list = from_drop_list
#    elif flag == "t":
#        drop_list = target_drop_list
    pLogger.debug("param: {}, {}, {}".format(name, cwd, cmdline))
    name_list = ['zabbix_server']
    if name in drop_list:
        return "drop"
    elif name == 'java':
        node = match_sort('java', "[" + name + "]_" + cwd)
        return node
    elif name in name_list:
        node = name
        return node
    else:
        node = ' '.join(eval(cmdline)[:3])  # rename p_cmdline just use 3 field
        return node


def match_nodes(connection_table, r_ip, r_port, server_uuid):
    """
    # ip node match
    TIME-WAIT  0      0      127.0.0.1:47618              127.0.0.1:8097
    TIME-WAIT  0      0      ::ffff:127.0.0.1:8069        ::ffff:127.0.0.1:50080
    """
    if r_ip == '127.0.0.1':
        match_sql_cmd = "select L.l_ip, L.l_port, L.p_cmdline, L.p_cwd, L.p_name "\
            "FROM {} L where L.l_ip = {!r} and L.l_port = {!r} and L.server_uuid = {!r} limit 1".format(
                connection_table, r_ip, r_port, server_uuid)
    else:
        match_sql_cmd = "select L.l_ip, L.l_port, L.p_cmdline, L.p_cwd, L.p_name "\
            "FROM {} L where L.l_ip = {!r} and L.l_port = {!r} limit 1".format(
                connection_table, r_ip, r_port)
    match_node = db_fetchall(match_sql_cmd, fetch='one')
    return match_node


def connection_process(connection):
    """
    process connection.
    if connection is a listen, drop it,

    """
    c_r_ip = connection["r_ip"]
    c_r_port = connection["r_port"]

    if c_r_ip == 'None' or c_r_ip is None or c_r_ip == ' ':
        return
    else:
        # c_l_ip = connection['l_ip']
        # c_l_port = connection["l_port"]
        c_p_name = connection['p_name']
        c_p_cwd = connection['p_cwd']
        c_p_cmdline = connection['p_cmdline']
        c_id = connection['id']
        flag = connection['flag']
        c_server_uuid = connection['server_uuid']
        pLogger.debug("\n{0}\nprocess id: {3} "
                      "connection is {1!r}, type: {2!r}, with flag {4!r}, type(flag)=> {5!r}"
                      .format(identify_line,
                              connection,
                              type(c_p_cmdline),
                              c_id,
                              flag,
                              type(flag)
                              )
                      )
        c_result = node_match(c_p_name, cwd=c_p_cwd, cmdline=c_p_cmdline)

        match_node = match_nodes(connection_table, c_r_ip, c_r_port, c_server_uuid)
        if match_node:
            pLogger.debug("match_node is : {}".format(match_node))
            m_p_cmdline = match_node['p_cmdline']
            m_p_cwd = match_node['p_cwd']
            m_p_name = match_node['p_name']
            pLogger.debug("match_node: {}, {}, {}".format(m_p_name, m_p_cwd, m_p_cmdline))
            m_result = node_match(m_p_name, cwd=m_p_cwd, cmdline=m_p_cmdline)
        else:
            convert_node = c_r_ip + ':' + c_r_port
            pLogger.debug("convert_node with port {!r}".format(convert_node))
            m_result = convert_node
        pLogger.debug("c_result=>{!r}, m_result=>{!r}".format(c_result, m_result))

        if c_result == "drop" or m_result == 'drop':
            pLogger.warn("process {} has connection {} are not needed, drop.".format(c_p_name, m_result))
            pLogger.debug("drop item is : {}".format(connection))
            return
        else:
            if flag == 1:
                from_node = c_result
                target_node = m_result
            elif flag == 0:
                from_node = m_result
                target_node = c_result
            else:
                pLogger.error("flag is needed!")
                return
        # finally from_node, target_node
        pLogger.debug("{}\nfrom_node :{!r} \ntarget_node: {!r}".format(identify_line, from_node, target_node))
        # time.sleep(1)
        return from_node.strip(), target_node.strip()


def fetch_list_process(result_tuple):
    pLogger.debug('result_tuple is {!r}'.format(result_tuple))
    if result_tuple:
        fetch_list.append(result_tuple)


def get_relation_list_from_db():
    """
    ip v,port v: connection match listen
    ip v,port x: listen program exit after collect connections
    ip x,port v: this explains nothing
    ip x,port x: this is a out server
    """
    # has listen program
    connections_sql_cmd = "SELECT * FROM {}".format(
        connection_table)
    connections_fetchall = db_fetchall(connections_sql_cmd, fetch='all')
    # pLogger.debug("connections fetch is: {!r}".format(connections_fetchall))
    return connections_fetchall


@db_close
def process_ralation(connections):
    # pool = multiprocessing.Pool(processes=4)
    pLogger.info("Run connection_process with PID {!r}".format(os.getpid()))
    now_process_num = 0
    for con in connections:
        now_process_num += 1
        if not now_process_num % 1000:
            pLogger.info("Now process No. => {!r}".format(now_process_num))
        # pool.apply_async(connection_process, args=(con,), callback=fetch_list_process)
        from_to_node_tuple = connection_process(con)
        fetch_list_process(from_to_node_tuple)
    # pLogger.info('Waiting for all processes done...')
    # pool.close()
    # pool.join()
    pLogger.info("All processes done!")


@spend_time
@start_end_point(SCRIPT_NAME)
@script_head
def main():
    try:
        connections = get_relation_list_from_db()
        process_ralation(connections)
        edges_list = list(set(fetch_list))
        pLogger.info("edges_list len {!r}".format(len(edges_list)))
        pickle_to_file(edges_list, netgraph_path)
    except Exception:
        traceback.print_exc()
    else:
        load_draw()


if __name__ == "__main__":
    main()
