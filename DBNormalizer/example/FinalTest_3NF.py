# -*- coding: utf-8 -*-
# 示例：连接真实数据库(PostgreSQL)，对库中每张表：挖掘 FD -> 求最小覆盖 -> 求候选键 -> 生成 3NF 分解。
# 依赖本地 PostgreSQL 库 dbnormalizer_test，需要自行调整连接串。
# 运行方式：python -m DBNormalizer.example.FinalTest_3NF
__author__ = 'Paris'

from DBNormalizer.example.relations import readDB_schema
from DBNormalizer.model.SQLParser import *
from DBNormalizer.model.Decomp import *

N=Normalization()       # 规范化对象
D=Decomposition()       # 分解对象

# 连接 PostgreSQL 并反射读取模式
db = create_engine('postgresql://humberto:@localhost/dbnormalizer_test')
insp = inspect(db)
meta = MetaData()
meta.reflect(bind=db)

relations_list = readDB_schema(insp)   # 用 inspector 构建 {表名: Relation}
names = list(relations_list.keys())    # 全部表名

# 逐表处理
for i in range(0,len(names)):
    nam = names[i]
    #print(nam)
    partitions_dict = get_table_partitions(nam, relations_list[nam].attributes, db)  # 每列取值分区
    #print(relations_list[nam].attributes)
    rltn = set(relations_list[nam].attributes)      # 该表属性全集
    print('Relation = ',rltn)
    #print (nam,'=',set(relations_list[nam].attributes))
    relations_list[nam].find_fds(partitions_dict)   # 依据数据挖掘 FD
    FDS = (relations_list[nam].fds)                 # 取出 FD 集
    #print(relations_list[nam])
    print('FDs = ',FDS)

    #FDs = FDependencyList([fd1, fd2, fd3, fd4,fd5])
    minFds=FDS.MinimalCover()                       # 最小覆盖
    print('MinCover = ',minFds)
    #allKeys = FDs.candidate_keys()
    allKeys=N.findCandKeys(rltn,minFds,FDS)         # 候选键
    print('Keys = ',allKeys)

    # for fd in minFds:
    #     lhs=set(fd.lh)
    #     rhs=set(fd.rh)

     #    if(N.check2NF(fd,lhs,rhs,allKeys)):
    #        print("2nf violation")
     #    if(N.check3NF(fd,lhs,rhs,allKeys)):
    #        print("3nf violation")
      #   if(N.checkBCNF(fd,lhs,rhs,allKeys)):
    #        print("BCNF violation")

    L=D.proposal3NF(rltn, minFds, FDS)              # 3NF 分解提议
    print('3NF - ',L)
    L.clear()
