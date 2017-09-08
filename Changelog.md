# 查询数据库并写入文件,使用\t分割
MySQL [yed_collect]> select * into outfile '/tmp/aac.csv' fields terminated by '\t' from service_listens_table;
Version 1.1.3:
	修改每次执行操作后db commit

