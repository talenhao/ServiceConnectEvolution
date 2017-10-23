#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2017-10-12 22:09:43
# @Author  : 郝天飞/Talen Hao (talenhao@gmail.com)
# @Link    : talenhao.github.io
# @Version : $Id$

import re
import shutil
import multiprocessing
import networkx as nx
import networkx.algorithms.traversal as nx_a_t
import networkx.drawing as nxd

# user module
from serconevo.pickleprocess import pickle_to_file
from serconevo.pickleprocess import pickle_from_file
from serconevo import netgraph_path
from serconevo import graph_nodes_bin
from serconevo import imgs_dir

# for log >>
import logging
import os
from serconevo.log4p import log4p
SCRIPT_NAME = os.path.basename(__file__)
# log end <<
pLogger = log4p.GetLogger(SCRIPT_NAME, logging.DEBUG).get_l()


def gv_graph(nxg, filename, node_name=None, fmt='pdf'):
    # save a dot file to local disk
    # nxd.nx_agraph.write_dot(nxg, imgs_dir + "/" + filename + '.dot')
    # convert to pygraphviz agraph object
    pgv_graph = nxd.nx_agraph.to_agraph(nxg)
    pgv_graph.graph_attr.update(rankdir="LR",  # 排布方向,左右
                                bgcolor='beige'  # 画布背景着色
                                )
    pgv_graph.node_attr.update(compound='true',
                               fillcolor='yellowgreen',  # 填充颜色 
                               style='filled',  # 填充
                               shape='folder',  # node图标形状
                               # shape='octagon',
                               # orientation='rotate',
                               orientation='landscape',
                               ratio='compress',
                               fontsize='10',  # 字体大小
                               fontname='DejaVu Sans Mono',  # 使用字体
                               remincross='true',
                               concentrate='false',
                               overlap='false',
                               rank='source',  # 等级
                               constraint='false',
                               clusterrank='none',
                               center='false',
                               imagepos='ml',
                               decorate='true',
                               fixedsize='false',  # 固定大小
                               height='.1'
                               )
    pgv_graph.edge_attr.update(splines='ortho',
                               # concentrate='true'
                               color='blue', 
                               penwidth='2.0',  # 线的粗细.
                               )
    if node_name:
        pgv_graph.add_node(node_name, fillcolor='orangered', shape='rounded', style='filled',
                           # gradientangle='90',
                           fontsize=10, labeljust='l',
                           height='.1'
                           )
    else:
        pLogger.warning("No center node.")
    pgv_graph.draw(imgs_dir + "/" + filename + '.' + fmt, format=fmt, prog='dot')
    pgv_graph.write(imgs_dir + "/" + filename + '.dot')


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


def draw_node(graph, source_node, graph_nodes):
    g = graph
    out_format = ['svg']
    pLogger.debug("source_node is {!r}".format(source_node))
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
    file_name = source_node.replace(' ', '_').replace('/', '_').replace('=', '')
    for fmt in out_format:
        gv_graph(g_new,
                 filename=file_name,
                 node_name=source_node,
                 fmt=fmt)
    pLogger.info("draw {!r} over.".format(source_node))


def traversal_nodes(graph):
    g = graph
    graph_nodes = set()
    pool = multiprocessing.Pool(processes=5)
    now_process_num = 0
    for source_node in g.node:
        now_process_num += 1
        pLogger.info("Now traversal node No. => {!r}".format(now_process_num))
        decide_ip_port = ip_port_decide(source_node)
        pLogger.debug("decide_ip_port is {!r}".format(decide_ip_port))
        if not decide_ip_port:
            source_node_replace = source_node.replace(' ', '_').replace('/', '_').replace('=', '')
            graph_nodes.add(source_node_replace)
            pool.apply_async(draw_node, args=(g, source_node, graph_nodes))
        else:
            pLogger.debug("ip:port {!r} match, drop drawing.".format(source_node))
    # pool.map_async(draw_node, g.node)
    pLogger.info('Waiting for all processes done...')
    pool.close()
    pool.join()
    pLogger.info("All processes done!")
    # save node list to file
    pLogger.info("graph_nodes: {}".format(graph_nodes))
    pickle_to_file(graph_nodes, graph_nodes_bin)


def draw_all(graph):
    pLogger.info('draw all nodes.')
    out_format = ['svg']
    for fmt in out_format:
        gv_graph(graph, filename='all', fmt=fmt)
    pLogger.debug('draw all nodes over.')


def draw_from_pickle(pickle_load):
    # pickle
    gv = graph_dot(pickle_load)
    # draw
    traversal_nodes(gv)
    draw_all(gv)


def load_draw():
    if not os.path.exists(imgs_dir):
        os.makedirs(imgs_dir)
        pLogger.debug("imgs_dir {} not exists, create it.".format(imgs_dir))
    elif os.listdir(imgs_dir):
        shutil.rmtree(imgs_dir)
        os.makedirs(imgs_dir)
        pLogger.debug("imgs_dir {} is not empty, to clean it.".format(imgs_dir))
    pickle_load = pickle_from_file(netgraph_path)
    draw_from_pickle(pickle_load)


def main():
    load_draw()


if __name__ == '__main__':
    main()
