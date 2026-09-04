# -*- coding: utf-8 -*-
# 示例：连接真实 PostgreSQL 数据库 -> 为每张表挖掘 FD -> 计算覆盖/候选键/范式 -> 执行 BCNF 分解，
# 并把分解出的子关系注册为独立的 Relation 对象（与 GUI/Model 主流程类似，但独立演示）。
# 需要本地库 dbnormalizer_test 与其中的 employee_project 等表。
# 运行方式：python -m DBNormalizer.example.findFDS_example2
__author__ = 'Nantes'

from DBNormalizer.example.relations import readDB_schema
from DBNormalizer.model.SQLParser import *
from DBNormalizer.model.Decomp import *
from DBNormalizer.model.Relation import *


#postgresql://user:password@localhost/mydatabase
db = create_engine('postgresql://humberto:@localhost/dbnormalizer_test')   # 连接数据库
insp = inspect(db)
meta = MetaData()
meta.reflect(bind=db)

relations_list = readDB_schema(insp)   # 从数据库构建 {表名: Relation}
names = list(relations_list.keys())

# 第一段：逐表挖掘 FD
for i in range(0,len(names)):
    nam = names[i]
    partitions_dict = get_table_partitions(nam, relations_list[nam].attributes, db)  # 每列取值分区
    relations_list[nam].find_fds(partitions_dict)    # 依据数据挖掘 FD
#    print(partitions_dict)
    #print(relations_list[nam])

print(relations_list)

# Lets try to compute NF:
# 第二段：计算每张表的最小覆盖、候选键与范式
for nam in names:
    relations_list[nam].set_canonical_cover()    # 最小覆盖
    relations_list[nam].set_candidate_keys()     # 候选键
    relations_list[nam].set_normalization()      # 范式判定
    print("----------------------------")
    print(relations_list[nam])

print("=======================")

# 第三段：逐表执行 BCNF 分解并把子关系注册为 Relation
dec = Decomposition()
decomposition_dic = {}
for name in relations_list.keys():
    rel = relations_list[name]
    attr = rel.attributes
    canonical_cover = rel.canonical_cover

    # Decomposition proposal:
    dec_proposal = dec.proposalBCNF(set(attr), canonical_cover)   # BCNF 分解提议
    # Saves the decomposition in a dictionary:
    decomposition_dic[name] = {}    # 保存该表的分解结果
    i = 1
    for tup in dec_proposal:
        sub_name = name + '_' + str(i)          # 子表名
        new_attr = list(tup[0])                 # 子表属性
        new_fds = FDependencyList(tup[1])       # 子表 FD
        new_relation = rel.sub_relation(sub_name, new_attr, new_fds)   # 构建子关系
        new_relation.set_canonical_cover()      # 补算子关系指标
        new_relation.set_candidate_keys()
        new_relation.set_normalization()
        decomposition_dic[name][sub_name] = new_relation
        i += 1

# 打印演示结果
print(relations_list[name])
print(decomposition_dic['employee_project']['employee_project_1'])
print(decomposition_dic['employee_project']['employee_project_2'])
