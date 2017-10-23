# 查询数据库并写入文件,使用\t分割
MySQL [yed_collect]> select * into outfile '/tmp/aac.csv' fields terminated by '\t' from service_listens_table;
Version 1.1.3:
	修改每次执行操作后db commit
Version 1.2.0
	修改数据结构,service_connections_table中unique key中添加local_ip;修改agent自动判断是listen还是connection表操作,两个表的字段数目不再一致.修改代码方便以后扩容.
Version 1.2.3
	原service_listens_table插入l_ip,l_port为set数据结构,现拆分为多条记录
Version 2017.9.11.5
	修复ip转ipv4
Version 2017.9.11.6
	修复connection为本机ip地址时无法匹配service_listens_table问题;连接127.0.0.1与::1的替换为本机其它ip
Version 2017.9.18.02
	修复cmdline中包含@#号时报数据库语法error的问题
Version 2017.9.19.04
	分割netgraph 画图与dot产生
Version 2017.9.20.05
	调整netgraph函数
Version 2017.9.29.20
	添加收集连接到服务的链接收集
Version 2017.9.30.21
	修改get_relation_list_from_db的算法
Version 2017.9.30.22
	netgraph模块使用多线程池处理
Version 2017.10.02.22
	netgraph模块使用多线程池处理,使用sscursor有点问题,回退


* 9fca63e -  支持点击每个节点进入相应的子交互图 - talenhao
* 43cd543 - 
* 357c27c - 
* d517be0 -  添加raddr lo的判断,替换为本机ip - talenhao
* 02ecd4f -  netgraph work ok. - talenhao
* 9671df9 -  fix进程有多个listen port时只收集第一个,其它会忽略的bug - talenhao
* daa0b5a -  use TimedRotatingFileHandler - talenhao
* eb6ace2 -  梳理connection process 流程 - talenhao
* a8aec89 -  ipv6 ipv4 listen only import2db once; drop duplicate listening port. - talenhao
* 8b057f1 -  add cocket connection detect - talenhao
* 0e25b7d -  to determine connected status. - talenhao
* 633c99c -  fix l_ip is a str, add decide l_ip_set. - talenhao
* 31da0ef -  change l_ip use local host ip - talenhao
* d59e991 -  use get_host_ip replace get_server_ip, exclude ipv6 - talenhao
* 5845c7a -  add drawgrapy module - talenhao
* cc26c2c -  process 127.0.0.1 raddr; drop ip:port drawing; process None:None raddr - talenhao
* 7778fe3 -  exclude some tcp status - talenhao
* e741bb0 -  process all connections; default use pdf to draw; use dictcursor... - talenhao
* 0ada107 -  agent collect all connections; use new table - talenhao
* 922fc5b -  old algorithms. - talenhao
* f191fc0 -  修改get_relation_list_from_db算法,处理连接到进程的连接 - talenhao
* 2bcb775 -  update version - talenhao
* bd6cc7b -  agent add connect in collect. - talenhao
* 526b1bd -  add getopt to process config file and pickle file - talenhao
* ad89f65 -  add pickle model process - talenhao
* 535fe60 -  add pickle collect model used when can't connect to the mysql server. - talenhao
* f1918be -  add function process_before_insert_db - talenhao
* a15fd96 -  data/solr match - talenhao
* 58974e3 -  解决接收大量数据文件客户端内存消耗尽,被kill的问题 - talenhao
* 72210ee -  use Unbuffered Cursor - talenhao
* 56a6362 -  fix date to data - talenhao
* 4f88f70 -  调整log打印 - talenhao
* 1bf5516 -  调整config.ini的获取变量 - talenhao
* e2fe497 -  调整config.ini的获取变量,netgraph函数调整 - talenhao
* 1cc307d -  add netgraph module - talenhao
* fe73576 -  add udp listen collect - talenhao
* 8a5da17 -  reduce import2db statement - talenhao
* fdf6d2f -  修改数据结构,service_connections_table中unique key中添加local_ip;修改agent自动判断是listen还是connection表操作,两个表的字段数目不再一致.修改代码方便以后扩容. - talenhao
* fd1df75 -  change tips of db commit - talenhao
* bec8928 -  when commit show sql cmd - talenhao
* b96477f -  commit after execution - talenhao
* bfbd302 -  serconevo packages, use wheel. - talenhao
*   f313195 -  Merge branch 'salt' - talenhao
|\  
| * 661bfea - 
* | a1c21f1 -  add log4p,model __init__ - talenhao
* | bc0f76b -  create log4p directory - talenhao
* | ed952f4 -  create directory model - talenhao
* | 70e1a52 -  change .gitignore - talenhao
* |   db497cb -  Merge branch 'agent' - talenhao
|\ \  
| * | 079cd58 - 
| * | 61547ca -  change to agent module - talenhao
| * | 549e00d -  version - talenhao
| * | b780f95 -  nothing - talenhao
| * | 29da808 -  add start_end_point decorater - talenhao
* | |   ebebe7d -  Merge branch 'salt' - talenhao
|\ \ \  
| | |/  
| |/|   
| * | 0541fd2 -  create salt directory,rm file - talenhao
| * | 6fc4934 -  create salt directory - talenhao
| * | 319c63e -  delete no require pip install module - talenhao
| * | e3edff6 -  if sce_requirements.txt changed, auto execute pip install - talenhao
| * | 815679f -  add sce_requirements.txt,write prepare.sls - talenhao
| * | 5b9959d -  create prepare.sls - talenhao
| * | cfe9d11 -  create init.sls - talenhao
| |/  
* | 0a172fa -  change Changelog.md - talenhao
|/  
| * e5b1782 - 
|/  
* 80d2894 -  fix local variable might be referenced before assignment tips - talenhao
* 915e0cd -  service_collect_agent.py works - talenhao
* 02e57bd -  Initial commit - 郝天飞
