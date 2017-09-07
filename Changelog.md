# 查询数据库并写入文件,使用\t分割
MySQL [yed_collect]> select * into outfile '/tmp/aac.csv' fields terminated by '\t' from service_listens_table;

