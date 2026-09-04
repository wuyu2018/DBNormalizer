# -*- coding: utf-8 -*-
# Model：整个应用的模型层/业务中枢。
# 职责：
#   - 管理与数据库(MySQL)的连接（用户名/主机等参数、SQLAlchemy engine）
#   - 导入数据库模式(每张表 -> Relation 对象)并基于数据自动发现 FD
#   - 维护全部关系字典 relations、以及“原始关系名”列表
#   - 供视图层使用的各种查询接口（NF/候选键/最小覆盖/FD/schema 等）
#   - 驱动规范化分解（3NF/BCNF）并把结果写入 relations 与 decomposition_match
#   - 依据分解结果生成新表的 SQL(DDL) 脚本 Queries.sql
# 该文件是“连接数据库 + 规范化”工作流的核心协调者。
__author__ = 'Nantes'

from DBNormalizer.model.Relation import Relation
from DBNormalizer.model.SQLParser import get_table_partitions
from sqlalchemy import *
from sqlalchemy.schema import CreateTable
from DBNormalizer.model.FDependencyList import *
from DBNormalizer.model.Decomp import *


class Model():
    # 初始化模型状态
    def __init__(self):
        # 数据库连接参数
        self.username = None
        self.password = None
        self.host = 'localhost'     # 默认主机
        self.database = None
        self.port = None
        self.engine = None          # SQLAlchemy engine

        self.insp = None            # SQLAlchemy inspector（读取库结构的工具）
        self.meta_original = MetaData()  # 原始数据库元数据
        self.relations = {}         # {关系名: Relation 对象}（含分解出的新关系）
        self.original_relations_names = []  # 原始(数据库中的)关系名列表

        #self.meta_new = MetaData()
        # A dictionary with lists, each with the names of its decomposed relations
        # 记录每个原始关系分解出了哪些子关系：{原关系名: [子关系名, ...]}
        self.decomposition_match = {}



    # 核心：为每个原始关系计算 3NF/BCNF 分解提议，并把分解出的新关系注册进 self.relations
    def compute_normalization_proposal(self, decomp='3NF'):
        self.delete_BCNF_decomposition_proposal()  # 先删除上一次的分解结果
        decomposition_dic = {}
        for name in self.original_relations_names:
            dec = Decomposition()           # 每表新建一个 Decomposition 实例
            rel = self.relations[name]
            attr = rel.attributes           # 该表全部属性
            canonical_cover = rel.canonical_cover  # 最小覆盖
            # Decomposition proposal:
            dec_relation_list = []          # 记录此表分解出的子关系名

            # Caso en que no hay FDs   情况1：没有 FD -> 原样复制成一个新关系
            if len(rel.fds) == 0:
                sub_name = name + "_1"
                new_relation = rel.sub_relation(sub_name, attr)  # 构造同名属性的子关系
                self.relations[sub_name] = new_relation
                new_relation.set_candidate_keys()
                new_relation.set_normalization()
                decomposition_dic[name] = [sub_name]
            # 情况2：已经是 BCNF -> 无需分解，整表作为一个子关系
            elif rel.NF == 'BCNF':
                sub_name = name + "_1"
                new_relation = rel.sub_relation(sub_name, attr, rel.fds)
                self.relations[sub_name] = new_relation
                new_relation.set_canonical_cover()
                new_relation.set_candidate_keys()
                new_relation.set_normalization()
                new_relation.join_rhs_fds()
                new_relation.join_rhs_cc()
                decomposition_dic[name] = [sub_name]
            # 情况3：需要分解 —— 调用 Decomposition 得到 (属性集合, FD列表) 提议
            else:
                if decomp == '3NF':
                    print(canonical_cover)
                    dec_proposal = dec.proposal3NF(set(attr), canonical_cover, (rel.fds))
                else:
                    dec_proposal = dec.proposalBCNF(set(attr), canonical_cover)

                # Saves the decomposition in a dictionary:
                # 把每个提议的子关系转成真正的 Relation 对象（子表），补齐计算指标
                i = 1
                for tup in dec_proposal:
                    sub_name = name + '_' + str(i)
                    dec_relation_list.append(sub_name)   # 记录子关系名
                    new_attr = list(tup[0])              # 子关系的属性
                    new_fds = FDependencyList(tup[1])    # 子关系的 FD
                    new_relation = rel.sub_relation(sub_name, new_attr, new_fds)

                    # 为新子关系重新计算：最小覆盖 / 候选键 / 范式
                    new_relation.set_canonical_cover()
                    new_relation.set_candidate_keys()
                    new_relation.set_normalization()

                    # 合并相同左部的右部(仅美化展示)
                    new_relation.join_rhs_fds()
                    new_relation.join_rhs_cc()

                    self.relations[sub_name] = new_relation  # 注册进全局关系字典
                    i += 1
                decomposition_dic[name] = dec_relation_list
        self.decomposition_match = decomposition_dic  # 保存分解匹配关系


    # 删除上一次计算出的所有分解子关系（从 relations 字典中移除）
    def delete_BCNF_decomposition_proposal(self):
        print(self.decomposition_match)
        print(self.decomposition_match.keys())
        for rel_name in self.decomposition_match.keys():
            dec_list = self.get_decomposition_names(rel_name)
            for dec in dec_list:
                del self.relations[dec]

    # 把分解后的新表生成 CREATE TABLE 语句，写入 Queries.sql 文件
    def compute_sql_statements(self):
        meta_new = MetaData()
        filename = "Queries.sql"
        f = open(filename, 'w')      # 先清空文件
        f.write('\n')
        f.close()
        keys =list(self.decomposition_match.keys())   # 对每个原始关系的子关系生成建表语句
        f = open(filename,'a')
        for relation in keys:
            m = self.get_decomposition_names(relation)
            for subrelation in m:
                s = self.relations[subrelation].SQL_statement(meta_new)  # 构建 SQLAlchemy Table
                l = CreateTable(s)     # 转成 CREATE TABLE 文本
                print(l)
                f.write(str(l))
        f.close()



    # 保存数据库连接参数
    def set_db_connection_params(self, username, password, host, database, port):
        self.username = username
        self.password = password
        self.host = host
        self.database = database
        self.port = port

    # 连接 MySQL 并读取数据库元数据（表结构），构建 engine 与 inspector
    def get_metadata(self):
        # conn_string = 'postgresql://' + str(self.username) + ':' + str(self.password) + '@' + str(self.host) + '/' + \
        #               str(self.database)
        # MySQL 连接串（固定 3306 端口）
        conn_string = 'mysql+pymysql://' + str(self.username) + ':' + str(self.password) + '@' + str(
            self.host) + ':3306/' + \
                      str(self.database)
        print(conn_string)
        self.engine = create_engine(conn_string)   # 创建引擎
        self.meta_original.reflect(bind=self.engine)  # 反射读取全部表结构
        self.insp = inspect(self.engine)           # 创建 inspector

    # 把数据库里的每张表转换为 Relation 对象，保存进 relations
    def get_schema(self):
        db_schema = {}
        tables = self.insp.get_table_names()       # 获取所有表名
        for name in tables:
            att = self.insp.get_columns(name)              # 列信息
            pk = self.insp.get_pk_constraint(name)         # 主键信息
            unique = self.insp.get_unique_constraints(name) # 唯一约束
            rel = Relation(name, schema_attributes=att, schema_keys=pk, schema_unique=unique)
            db_schema[name] = rel

        self.original_relations_names = tables
        self.relations = db_schema

    # 对每张表：依据真实数据挖掘 FD，并计算最小覆盖/候选键/范式
    def append_fds(self):
        names = list(self.relations.keys())
        for i in range(0,len(names)):
            nam = names[i]
            print("-------------Reading:------------", nam)
            # 取得每列的取值分区(供 FD 挖掘)
            partitions_dict = get_table_partitions(nam, self.relations[nam].attributes, self.engine)
            print("---------------------------------")
            print(self.relations[nam])
            self.relations[nam].find_fds(partitions_dict)   # 挖掘 FD

            # Compute the canicalcover, candidate keys and normal form
            # 依次计算：最小覆盖、候选键、当前范式
            self.relations[nam].set_canonical_cover()
            self.relations[nam].set_candidate_keys()
            self.relations[nam].set_normalization()

            # 相同左部合并(展示用)
            self.relations[nam].join_rhs_fds()
            self.relations[nam].join_rhs_cc()
            #print(self.relations[nam])

    # “保存”时重新计算某关系的各项规范化指标（FD 被用户编辑后调用）
    def update_relation(self, relation_name):
        self.relations[relation_name].set_canonical_cover()
        self.relations[relation_name].set_candidate_keys()
        self.relations[relation_name].set_normalization()
        self.relations[relation_name].join_rhs_fds()
        self.relations[relation_name].join_rhs_cc()

    # 返回某关系的范式等级
    def get_NF(self, relation_name):
        return self.relations[relation_name].NF

    # 返回某关系的候选键
    def get_candidate_keys(self, relation_name):
        return self.relations[relation_name].candidate_keys

    # 返回某关系的最小覆盖
    def get_canonical_cover(self, relation_name):
        return self.relations[relation_name].canonical_cover

    # 返回某关系的全部 FD
    def get_fds(self,relation_name):
        return self.relations[relation_name].fds

    # 返回某原始关系的分解子关系名列表
    def get_decomposition_names(self, relation_name):
        return self.decomposition_match[relation_name]

    # 返回所有发生过分解的原始关系名
    def get_decomposition_names_all(self):
        l = []
        for i in self.decomposition_match:
            l.append(i)
        return l

    # 返回所有原始关系名
    def get_original_relations_names(self):
        return self.original_relations_names

    # 返回所有关系名（含分解子关系）
    def get_relation_names(self):
        return self.relations.keys()

    # 按名字取关系对象
    def get_relation(self, relation_name):
        return self.relations[relation_name]

    # 返回某关系的属性列表
    def get_relation_attributes(self, relation_name):
        return self.relations[relation_name].attributes

    # 删除指定下标处的 FD（返回被删除对象）
    def remove_fd_idx(self, relation_name, idx):
        rel = self.get_relation(relation_name)
        removed = rel.fds.remove_fd_idx(idx)
        return removed

    # 新增一条 FD（fd_dic 形如 {'lhs':'A,B','rhs':'C'}，逗号分隔转成列表）
    def add_fd(self, fd_dic, relation_name):
        rel = self.get_relation(relation_name)
        lhs = fd_dic['lhs'].split(",")
        lhs_format = [x.strip() for x in lhs]
        rhs = fd_dic['rhs'].split(",")
        rhs_format = [x.strip() for x in rhs]
        fd = FDependency(lhs_format, rhs_format)
        rel.fds_add(fd)

    # 计算某属性组合的闭包（attr_dic 形如 {'attr':'A,B'}）
    def get_attr_closure(self, attr_dic, relation_name):
        rel = self.get_relation(relation_name)
        attributes = attr_dic['attr'].split(",")
        attributes_format = [x.strip() for x in attributes]
        closure = rel.fds.attribute_closure(attributes_format)
        return closure

    # 返回某关系在指定范式(nf)下的违例 FD 列表
    def get_violation(self, relation_name, nf='2NF'):
        rel = self.get_relation(relation_name)
        if nf == '2NF':
            ret = rel.normalization.FDList2NF
        elif nf == '3NF':
            ret = rel.normalization.FDList3NF
        else:
            ret = rel.normalization.FDListBCNF
        return ret

    # 返回某关系的数据库列 schema 信息
    def get_relation_db_schema_attributes(self, relation_name):
        rel = self.get_relation(relation_name)
        return rel.db_schema_attributes

    # 返回某关系的唯一约束 schema
    def get_relation_db_schema_unique(self, relation_name):
        rel = self.get_relation(relation_name)
        return rel.db_schema_unique

    # 返回某关系的主键 schema
    def get_relation_db_schema_pk(self, relation_name):
            rel = self.get_relation(relation_name)
            return rel.db_schema_pk

    # 手动新增一个关系（GUI “Add Relation”）。重名返回 1，否则返回 0
    def add_user_relation(self, relation_name):
        if relation_name not in self.original_relations_names:
            self.original_relations_names.append(relation_name)
            self.relations[relation_name] = Relation(relation_name)
            return 0
        else:
            return 1


    # 手动为某关系新增属性（GUI “Add Attribute”）
    def add_user_relation_attribute(self, relation_name, attribute_name):
        rel = self.get_relation(relation_name)
        return rel.add_attributes(attribute_name)
