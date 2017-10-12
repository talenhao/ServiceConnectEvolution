#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2017-10-12 22:09:43
# @Author  : 郝天飞/Talen Hao (talenhao@gmail.com)
# @Link    : talenhao.github.io
# @Version : $Id$

import re
import pickle
import multiprocessing
import networkx as nx
import networkx.algorithms.traversal as nx_a_t
import networkx.drawing as nxd

# user module
from serconevo import identify_line
# for log >>
import logging
import os
from serconevo.log4p import log4p
SCRIPT_NAME = os.path.basename(__file__)
# log end <<
pLogger = log4p.GetLogger(SCRIPT_NAME, logging.DEBUG).get_l()


def pickle_from_file(pickle_file):
    pLogger.debug("{} pickle_file is:{!r}".format(
        identify_line, pickle_file))
    with open(pickle_file, 'rb') as load_file:
        return pickle.load(load_file)


def gv_graph(nxg, filename, node_name=None, fmt='pdf'):
    # save a dot file to local disk
    nxd.nx_agraph.write_dot(nxg, "dot/" + filename + '.dot')
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
    pgv_graph.draw("img/" + filename + '.' + fmt, format=fmt, prog='dot')


def graph_dot(node_list):
    """
    [root@backup138 netgraph]# grep 'g.DiGraph is' debug.log
    2017-10-12 19:29:43,445 DEBUG __init__.py +281 graph_dot [MainThread]: g.DiGraph is: {'name': 'all'}
    [root@backup138 netgraph]# grep 'nos:' debug.log
    2017-10-12 19:29:46,135 DEBUG __init__.py +285 graph_dot [MainThread]: nos: 11
    """
    # create directed graph
    # g = nx.MultiDiGraph(day="Friday")
    g = nx.DiGraph(name='all')
    pLogger.debug("g.DiGraph is: {!r}".format(g.graph))
    g.add_edges_from(node_list)
    # pLogger.debug("g.node : {!r}".format(g.node))
    # pLogger.debug("g.nodes: {!r}\ng.edges: {!r}".format(g.nodes(), g.edges()))
    pLogger.debug("nos: {}".format(g.number_of_selfloops()))
    # dfs
    return g


def ip_port_decide(string):
    """
    decide str is a ip:port
    """
    re_compile = re.compile(r'(?<![0-9])(?:(?:[0-1]?[0-9]{1,2}|2[0-4][0-9]|25[0-5])[.](?:[0-1]?[0-9]{1,2}|2[0-4][0-9]|25[0-5])[.](?:[0-1]?[0-9]{1,2}|2[0-4][0-9]|25[0-5])[.](?:[0-1]?[0-9]{1,2}|2[0-4][0-9]|25[0-5]))(?![0-9]):[0-9]{1,5}')
    try:
        re_match = re_compile.fullmatch(string)
        pLogger.debug("ip match: {!r}".format(re_match))
    except AttributeError:
        pLogger.debug("{} has no ip:port re compile!!".format(string))
    else:
        return re_match


def draw_node(graph, source_node):
    g = graph
    pLogger.debug("source_node is {!r}".format(source_node))
    decide_ip_port = ip_port_decide(source_node)
    if not decide_ip_port:
        pLogger.debug("decide_ip_port is {!r}".format(decide_ip_port))
        pLogger.debug("Begin to traversal {!r} deges use dfs".format(source_node))
        dfs_edges_result = nx_a_t.dfs_edges(g, source=source_node)
        pLogger.debug("Begin to reverse traversal {!r} deges use dfs".format(source_node))
        gr = g.reverse(copy=True)
        gr_dfs_edges_result = nx_a_t.dfs_edges(gr, source=source_node)
        pLogger.info("traversal ok!")

        # gv_graph(gr, filename='gr')
        follows = list(dfs_edges_result)
        leaders = list(gr_dfs_edges_result)
        pLogger.debug("follows type {}: {} \n leaders type {} :{}".format(
            type(follows), follows, type(leaders), leaders))
        pLogger.info("create new graph with {!r}".format(source_node))
        gr_new = nx.DiGraph(name='gr')
        gr_new.add_edges_from(leaders)
        pLogger.debug(gr_new.graph)
        g_new = gr_new.reverse(copy=True)
        g_new.add_edges_from(follows)
        pLogger.debug("g_new.graph is {!r}".format(g_new.graph))
        # draw a graph
        gv_graph(g_new,
                 filename=source_node.replace(' ', '-').replace('/', '_').replace('=', ''),
                 node_name=source_node,
                 fmt='pdf')
        pLogger.info("draw {!r} over.".format(source_node))
    else:
        pLogger.debug("ip:port {!r} match, drop drawing.".format(source_node))


def traversal_nodes(graph):
    g = graph
    pool = multiprocessing.Pool(processes=2)
    now_process_num = 0
    for source_node in g.node:
        now_process_num += 1
        pLogger.info("Now traversal node No. => {!r}".format(now_process_num))
        pool.apply_async(draw_node, args=(g, source_node,))
    # pool.map_async(draw_node, g.node)
    pLogger.info('Waiting for all processes done...')
    pool.close()
    pool.join()
    pLogger.info("All processes done!")


def draw_all(graph):
    pLogger.info('draw all nodes.')
    gv_graph(graph, filename='all')
    pLogger.debug('draw all nodes over.')


def draw_from_pickle(pickle_load):
    gv = graph_dot(pickle_load)
    # traversal_nodes(gv)
    draw_all(gv)


def main():
    pickle_load = pickle_from_file('fetch_list.bin')
    draw_from_pickle(pickle_load)


if __name__ == '__main__':
    main()
