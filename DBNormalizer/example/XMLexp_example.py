# -*- coding: utf-8 -*-
# 示例：XML 导出 —— 连接 PostgreSQL 库，逐表挖掘 FD、做 BCNF 分解，
# 然后把每个分解出的子表（属性+FD）写成 XML 文件。
# 需要自行调整数据库连接串与 exPath 输出目录。
# 运行方式：python -m DBNormalizer.example.XMLexp_example
__author__ = 'Paris'

from DBNormalizer.example.relations import readDB_schema
from DBNormalizer.model.SQLParser import *
from DBNormalizer.model.Decomp import *
from DBNormalizer.model.XMLIO import *

'''
The correct path to folder should be specified for exPath
'''
exPath="/Users/mariaslanova/PycharmProjects/DBNormalizer/DBNormalizer/DBNormalizer/XML/XML_export/"  # XML 输出目录

N=Normalization()       # 规范化对象
D=Decomposition()       # 分解对象
Xml=XmlParsing()        # XML 解析工具
db = create_engine('postgresql://mariaslanova:@localhost/Test1')  # 连接数据库
insp = inspect(db)
meta = MetaData()
meta.reflect(bind=db)

relations_list = readDB_schema(insp)   # 读取模式
names = list(relations_list.keys())    # 表名列表
tabNo=0                                # 输出表序号
for i in range(0,len(names)):
    nam = names[i]
    #print(nam)
    partitions_dict = get_table_partitions(nam, relations_list[nam].attributes, db)  # 列取值分区
    #print(relations_list[nam].attributes)
    rltn = set(relations_list[nam].attributes)      # 属性全集
    print('Relation = ',rltn)
    #print (nam,'=',set(relations_list[nam].attributes))
    relations_list[nam].find_fds(partitions_dict)   # 挖掘 FD
    FDS = (relations_list[nam].fds)
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

    L=D.proposalBCNF(rltn,minFds)                   # BCNF 分解
    for l in L:
        tabName="table"+str(tabNo)                  # 生成表名 table0, table1, ...
        S=list()
        for s in l[1]:                              # 把 FD 对象转成 (lhs,rhs) 元组
            S.append((s.lh,s.rh))
        # 把该子表的属性 + FD 写成 XML 文件
        Xml.writeTableToXML(tabName,list(l[0]),S,"Decomposition",exPath)
        S.clear()
        tabNo=tabNo+1
    L.clear()
