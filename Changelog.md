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
