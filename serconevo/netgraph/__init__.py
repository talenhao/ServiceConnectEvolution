# -*- coding: UTF-8 -*-
"""
# ******************************************************
# * author: "Talen Hao(天飞)<talenhao@gmail.com>"      *
# ******************************************************
"""
# todo menu

import traceback
import re

import networkx as nx
import networkx.algorithms.traversal as nx_a_t
import networkx.drawing as nxd

from serconevo.model import db_connect
from serconevo.agent.service_collect_agent import script_head
from serconevo.agent.service_collect_agent import db_close
from serconevo.agent.service_collect_agent import spend_time
from serconevo.agent.service_collect_agent import start_end_point

# for log >>
import logging
import os
from serconevo.log4p import log4p

SCRIPT_NAME = os.path.basename(__file__)
pLogger = log4p.GetLogger(SCRIPT_NAME, logging.DEBUG).get_l()
# log end <<


identify_line = "=*=" * 10

db_con = db_connect.DbInitConnect()
config_parser = db_con.python_config_parser
service_listens_table = config_parser.get("TABLE", "listen_table")
service_connections_table = config_parser.get("TABLE", "connection_table")


def db_fetchall(sql_cmd):
    pLogger.debug("SQL_CMD is =====> {!r}  __________".format(sql_cmd))
    db_con.cursor.execute(sql_cmd)
    pLogger.info("=====> DB operation command result: {!r}".format(db_con.cursor.rowcount))
    return db_con.cursor.fetchall()


def match_sort(project, string):
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


def get_relation_list_from_db():
    """
    ip v,port v: connection match listen
    ip v,port x: listen program exit after collect connections
    ip x,port v: this explains nothing
    ip x,port x: this is a out server
    :return:
    """
    fetch_list = []
    drop_list = ['ssh', 'sshd', 'whois']
    
    # has listen program
    # step1, from node process
    connections_has_target_sql_cmd = "SELECT c.c_ip, c.c_port, c.p_name, c.p_cwd, c.p_cmdline," \
                                     " l.p_name, l.p_cwd, l.p_cmdline" \
                                     " FROM {} c, {} l" \
                                     " WHERE c.c_ip = l.l_ip and c.c_port = l.l_port" \
        .format(service_connections_table,
                service_listens_table,
                )
    connections_has_target_fetchall = db_fetchall(connections_has_target_sql_cmd)
    for connection in connections_has_target_fetchall:
        c_p_name = connection[2]
        c_p_cwd = connection[3]
        c_p_cmdline = connection[4]
        l_p_name = connection[5]
        l_p_cwd = connection[6]
        l_p_cmdline = connection[7]
        pLogger.debug("\n{0}{0}\nconnection is {1!r}, type: {2!r}"
                      .format(identify_line,
                              connection,
                              type(c_p_cmdline)
                              )
                      )
        from_node = ' '.join(eval(c_p_cmdline))  # c.p_cmdline
        target_node = ' '.join(eval(l_p_cmdline))  # l.p_cmdline
        pLogger.debug("from_node source: {}  target_node source: {}".format(from_node, target_node))
        # step2, target node process
        if c_p_name in drop_list or l_p_name in drop_list:
            pLogger.warn("From {} to {} not needed, drop.".format(c_p_name, l_p_name))
            pLogger.debug("drop item is : {}".format(connection))
            continue
        if c_p_name == 'java':
            from_node = match_sort('java', from_node + "=" + c_p_cwd)
        elif c_p_name == 'zabbix_server':
            from_node = c_p_name
        else:
            from_node = ' '.join(eval(c_p_cmdline)[:3])  # rename p_cmdline just use 3 field
        if l_p_name == 'java':
            target_node = match_sort('java', target_node + '=' + l_p_cwd)
        elif l_p_name == "zabbix_server":
            target_node = l_p_name
        else:
            target_node = ' '.join(eval(l_p_cmdline)[:3])  # rename p_cmdline just use 3 field
        # finally from_node, target_node
        pLogger.debug("{}\nfrom_node :{!r} \ntarget_node: {!r}".format(identify_line, from_node, target_node))
        fetch_list.append((from_node.strip(), target_node.strip()))

    # no listen program
    # step1, from node process
    connections_no_target_sql_cmd = "SELECT c.c_ip, c.c_port, c.p_name, c.p_cwd, c.p_cmdline" \
                                    " FROM {} c" \
                                    " WHERE NOT EXISTS" \
                                    " (SELECT l.id FROM {} l" \
                                    "   where c.c_ip = l.l_ip and c.c_port = l.l_port" \
                                    " )"\
        .format(service_connections_table,
                service_listens_table,
                )
    connections_no_target_fetchall = db_fetchall(connections_no_target_sql_cmd)
    for connection in connections_no_target_fetchall:
        c_p_ip = connection[0]
        c_p_port = connection[1]
        c_p_name = connection[2]
        c_p_cwd = connection[3]
        c_p_cmdline = connection[4]
        pLogger.debug("\n{0}{0}\nconnection is {1!r}, type: {2!r}"
                      .format(identify_line,
                              connection,
                              type(c_p_cmdline)
                              )
                      )
        from_node = ' '.join(eval(c_p_cmdline))  # c.p_cmdline
        target_node = c_p_ip + ":" + c_p_port
        pLogger.debug("from_node source: {}  target_node source: {}".format(from_node, target_node))
        # step2, target node process
        if c_p_name in drop_list or l_p_name in drop_list:
            pLogger.warn("From {} to {} not needed, drop.".format(c_p_name, l_p_name))
            continue
        if c_p_name == 'java':
            from_node = match_sort('java', from_node + "=" + c_p_cwd)
        elif c_p_name == 'zabbix_server':
            from_node = c_p_name
        else:
            from_node = ' '.join(eval(c_p_cmdline)[:3])  # rename p_cmdline just use 3 field
        # finally from_node, target_node
        pLogger.debug("{}\nfrom_node :{!r} \ntarget_node: {!r}".format(identify_line, from_node, target_node))
        fetch_list.append((from_node.strip(), target_node.strip()))
    pLogger.debug("{}\nfetch_list is :\n {!r}".format(identify_line, fetch_list))
    return fetch_list


def gv_graph(nxg, filename, node_name=None, fmt='png'):
    # save a dot file to local disk
    nxd.nx_agraph.write_dot(nxg, "dot/"+filename+'.dot')
    # convert to pygraphviz agraph object
    pgv_graph = nxd.nx_agraph.to_agraph(nxg)
    pgv_graph.graph_attr.update(rankdir="LR")
    pgv_graph.node_attr.update(fillcolor='green:yellow',
                               style='filled',
                               shape='polygon',
                               # orientation='rotate',
                               orientation='landscape',
                               ratio='compress',
                               fontsize='8',
                               remincross='true',
                               concentrate='false',
                               compound='true',
                               overlap='false',
                               rank='source',
                               constraint='false',
                               clusterrank='none',
                               center='false',
                               imagepos='ml',
                               decorate='true',
                               fixedsize='false',
                               height='.1'
                               )
    pgv_graph.edge_attr.update(splines='compound', concentrate='true')
    if node_name:
        pgv_graph.add_node(node_name, fillcolor='red:yellow', shape='octagon', style='filled',
                           # gradientangle='90',
                           fontsize=10, labeljust='l',
                           height='.1')
    else:
        pLogger.warning("No center node.")
    pgv_graph.draw("img/"+filename+'.'+fmt, format=fmt, prog='dot')


def graph_dot(node_list):
    # create directed graph
    # g = nx.MultiDiGraph(day="Friday")
    g = nx.DiGraph(name='all')
    pLogger.debug("g.DiGraph is: {!r}".format(g.graph))
    g.add_edges_from(node_list)
    pLogger.debug("g.node : {!r}".format(g.node))
    pLogger.debug("g.nodes: {!r}\ng.edges: {!r}".format(g.nodes(), g.edges()))
    pLogger.debug("nos: {}".format(g.number_of_selfloops()))
    # dfs
    return g


def draw_node(graph):
    g = graph
    for source_node in g.node:
        dfs_edges_result = nx_a_t.dfs_edges(g, source=source_node)
        gr = g.reverse(copy=True)
        gr_dfs_edges_result = nx_a_t.dfs_edges(gr, source=source_node)

        # gv_graph(gr, filename='gr')
        follows = list(dfs_edges_result)
        leaders = list(gr_dfs_edges_result)
        pLogger.debug("\nfollows type{}: {}\ntype {} leaders: {}".format(
            type(follows), follows, type(leaders), leaders))
        gr_new = nx.DiGraph(name='gr')
        gr_new.add_edges_from(leaders)
        pLogger.debug(gr_new.graph)
        g_new = gr_new.reverse(copy=True)
        g_new.add_edges_from(follows)
        pLogger.debug(g_new.graph)
        # draw a graph
        gv_graph(g_new,
                 filename=source_node.replace(' ', '-').replace('/', '_').replace('=', ''),
                 node_name=source_node)


def draw_all(graph):
    gv_graph(graph, filename='all')


@spend_time
@start_end_point(SCRIPT_NAME)
@script_head
@db_close
def main():
    try:
        edges_list = get_relation_list_from_db()
    except Exception as e:
        traceback.print_exc()
    else:
        gv = graph_dot(edges_list)
        draw_node(gv)
        draw_all(gv)


if __name__ == "__main__":
    main()
