# -*- coding: utf-8 -*-
# Relation：关系(表)类。表示一个关系模式，把一个关系的所有状态聚合在一起：
#   - 属性集 attributes
#   - 函数依赖 fds、最小覆盖 canonical_cover
#   - 主键/唯一约束等数据库 schema 信息(db_schema_*)
#   - 候选键 candidate_keys、当前范式 NF、各种范式违例列表(normalization)
# 提供：重新计算覆盖/候选键/范式、按数据库数据挖掘 FD、生成 SQL 建表、
#      以及生成"子关系"(用于分解后建立新表)等能力。
__author__ = 'Nantes'
from DBNormalizer.model.FDependencyList import *
from DBNormalizer.model.findFDs import find_fds
from DBNormalizer.model.SQLParser import *
from DBNormalizer.model.Normalization import *


class Relation:
    # 构造函数：
    #   attributes        手动输入时的属性名列表
    #   schema_attributes 由数据库导入的列信息(SQLAlchemy 字典列表)，此时会从中提取属性名
    #   schema_keys       数据库主键信息
    #   schema_unique     数据库唯一约束信息
    def __init__(self, name, attributes=None, schema_attributes=None, schema_keys=None, schema_unique=None):
        self.name = name            # 关系名
        self.attributes = attributes # 属性名列表
        self.key = []               # 主键属性(由 db schema 得到)
        self.unique = []            # 唯一约束属性(由 db schema 得到)
        self.fds = FDependencyList()  # 该关系的函数依赖集合
        self.NF = None              # 该关系满足的范式(1NF/2NF/3NF/BCNF/NoFDs)

        # Normalization 状态（各种违例 FD 列表）
        self.normalization = Normalization()
        self.NF = None              # 当前范式
        self.candidate_keys = []    # 候选键(每个是 set)
        self.canonical_cover = FDependencyList()  # 最小覆盖

        # 数据库 schema 原始信息
        self.db_schema_attributes = schema_attributes
        self.db_schema_pk = schema_keys
        self.db_schema_unique = schema_unique

        # 若提供了数据库列信息，则从中抽取出"属性名"列表
        if schema_attributes:
            self.attributes = get_schema_attribute_property(self.db_schema_attributes, att_property='name')
        # 若提供了主键信息，则抽出主键列
        if schema_keys:
            self.key = get_schema_keys(self.db_schema_pk)
        # 若提供了唯一约束信息，则抽出唯一列
        if schema_unique:
            self.unique = get_schema_unique(self.db_schema_unique)

    # 打印关系全部信息（便于调试）
    def __str__(self):
        return str("Name: ") + str(self.name) + "\n" + "Attributes: " + str(self.attributes) + \
               "\n" + "PK: " + str(self.key) + "\n" + "Unique: " + str(self.unique) + "\n"\
               + "FDS: " + str(self.fds) + "\n" + "CC:" + str(self.canonical_cover) + "\n" + "Cand keys:" + \
               str(self.candidate_keys) + "\n" + "NF: " + str(self.NF)

    # 合并 canonical cover 中左部相同的 FD 的右部（如 A->B、A->C 合并成 A->BC），
    # 使展示更紧凑，且不影响语义。
    def join_rhs_cc(self):
        new_fds = FDependencyList()
        old_fds = self.canonical_cover[:]
        while len(old_fds) > 0:
            fds_sel = old_fds.pop()       # 每次取出一条 FD
            i = 0
            while i < len(old_fds):       # 在剩余中找相同左部者合并右部
                fd = old_fds[i]
                if fds_sel.lh == fd.lh:
                    fds_sel.rh = fds_sel.rh + fd.rh
                    old_fds.pop(i)
                i+=1
            new_fds.append(fds_sel)
        self.canonical_cover = new_fds

    # 合并 self.fds 中左部相同的 FD 的右部（同上，作用于 fds）
    def join_rhs_fds(self):
        new_fds = FDependencyList()
        old_fds = self.fds[:]
        while len(old_fds) > 0:
            fds_sel = old_fds.pop()
            i = 0
            while i < len(old_fds):
                fd = old_fds[i]
                if fds_sel.lh == fd.lh:
                    fds_sel.rh = fds_sel.rh + fd.rh
                    old_fds.pop(i)
                i+=1
            new_fds.append(fds_sel)
        self.fds = new_fds

    # 以下 4 个 getter 用于从数据库 schema 读取各列的属性（类型/自增/可空/默认值）
    def get_attributes_type(self, attr_name=None):
        return get_schema_attribute_property(self.db_schema_attributes, att_property='type', attr_name=attr_name)

    def get_attributes_autoincrement(self, attr_name=None):
        return get_schema_attribute_property(self.db_schema_attributes, att_property='autoincrement',
                                             attr_name=attr_name)

    def get_attributes_nullable(self, attr_name=None):
        return get_schema_attribute_property(self.db_schema_attributes, att_property='nullable', attr_name=attr_name)

    def get_attributes_default(self, attr_name=None):
        return get_schema_attribute_property(self.db_schema_attributes, att_property='default', attr_name=attr_name)

    # 手动添加属性：去重处理，成功返回 0，重复返回 1
    def add_attributes(self, attributes):
        if self.attributes is None:       # 首次添加 -> 创建列表
            self.attributes = [attributes]
            return 0
        elif attributes not in self.attributes:
            self.attributes.append(attributes)
            return 0
        else:
            return 1                      # 属性已存在

    # 计算并保存最小覆盖(有 FD 时才计算)
    def set_canonical_cover(self):
        if len(self.fds) > 0:
            self.canonical_cover = self.fds.MinimalCover()
            self.join_rhs_cc()            # 相同左部合并显示

    # 计算候选键：有覆盖时用 Normalization.findCandKeys；否则把全部属性视为唯一候选键
    def set_candidate_keys(self):
        if len(self.canonical_cover) != 0:
            self.candidate_keys = self.normalization.findCandKeys(set(self.attributes), self.canonical_cover, self.fds)
        else:
            self.candidate_keys = [set(self.attributes)]

    # 判断范式等级：对每条 FD 分别检查 2NF/3NF/BCNF 违例，
    # 然后根据"最早出现的违例"来判定该关系达到的最高范式。
    def set_normalization(self):
        if len(self.canonical_cover) != 0:
            fds_right_singleton = self.canonical_cover.makeRightsingleton()  # 先拆成右部单属性便于逐条判断

            self.normalization.FDListBCNF = FDependencyList()  # 清空上次的结果
            self.normalization.FDList3NF = FDependencyList()
            self.normalization.FDList2NF = FDependencyList()
            for fd in fds_right_singleton:
                lhs=set(fd.lh)
                rhs=set(fd.rh)
                self.normalization.check2NF(fd,lhs,rhs, self.candidate_keys)   # 检查 2NF 违例
                self.normalization.check3NF(fd, lhs, rhs, self.candidate_keys) # 检查 3NF 违例
                self.normalization.checkBCNF(fd, lhs, rhs, self.candidate_keys) # 检查 BCNF 违例

            # 判定范式：有 2NF 违例->只达 1NF；否则有 3NF 违例->2NF；
            # 否则有 BCNF 违例->3NF；都无->BCNF
            if len(self.normalization.FDList2NF) != 0:
                self.NF = '1NF'
            elif len(self.normalization.FDList3NF) != 0:
                self.NF = '2NF'
            elif len(self.normalization.FDListBCNF) != 0:
                self.NF = '3NF'
            else:
                self.NF = 'BCNF'
        else:
            # 没有任何 FD：清空违例并把范式标记为 NoFDs
            self.normalization.FDListBCNF = FDependencyList()
            self.normalization.FDList3NF = FDependencyList()
            self.normalization.FDList2NF = FDependencyList()
            self.NF = 'NoFDs'

    # 追加 FD：支持追加单个 FD 对象或整个 FDependencyList
    def fds_add(self, fd):
        if type(fd) is FDependencyList:
            self.fds.extend(fd)
        if type(fd) is FDependency:
            self.fds.append(fd)

    # 删除某个 FD 对象
    def fds_remove(self, fd):
        if type(fd) is FDependency:
            self.fds.remove(fd)

    # 从数据库数据中挖掘 FD（由 findFDs 模块完成），再合并相同左部
    def find_fds(self, db_partition, test_mode=False, pk=[], uk=[]):
        """
        Calls find_fds from SQLParser and computes minimal cover
        :param db_partition:
        """
        fds = FDependencyList()
        # find_fds 返回 {rhs: [满足的 lhs 列表]}
        fds_in_rel = find_fds(self.attributes, db_partition, test_mode, pk=self.key, uk=self.unique)
        for rhs in fds_in_rel.keys():
            if fds_in_rel[rhs]:
                for lhs in fds_in_rel[rhs]:
                    fds.append(FDependency(lhs, [rhs]))
        #self.fds = fds.MinimalCover()
        self.fds = fds
        self.join_rhs_fds()               # 相同左部合并显示

    # 依据该关系的 schema 信息构造一个 SQLAlchemy Table 对象，
    # 可用于生成 CREATE TABLE 语句或直接在数据库中建表。
    def SQL_statement(self, metadata):
        """
        Returns an object of class Table (see parse_table function) that can be used to send the CREATE TABLE statement
        to the database. This method needs, at least, the schema_attributes attribute.
        :param metadata: metadata (SQLAlchemy)
        :return: and object of class table
        """
        name = self.name
        column_schema = self.db_schema_attributes  # Mandatory
        pk_schema = self.db_schema_pk
        unique_schema = self.db_schema_unique
        return parse_table(name, metadata, column_schema_list=column_schema, pk_schema=pk_schema,
                           unique_schema=unique_schema)

    # 生成"子关系"：只保留 over_attributes 中的列（及其在数据库中的类型等信息），
    # 若主键/唯一约束不完全落在这些列上则被丢弃。可选地传入该子关系上的 FD。
    # 供规范化分解后构造新关系使用。
    def sub_relation(self, name, over_attributes, fds=None):
        """
        Returns a sub-relation over the attributes specified. The pk and unique constraints are dropped if
        they are not defined completely in the sub-relation. If the schema_attributes, schema_pk and schema_unique
        are defined, the method will use them to obtain the new sub-relation.
        :param name: name of the new relation
        :param over_attributes: the attributes that the sub-relation must contain
        :return:
        """
        if self.db_schema_attributes:   # 有数据库 schema 信息 -> 按列名过滤出新子关系的 schema
            new_schema_attr = decompose_schema_attributes(self.db_schema_attributes, over_attributes)
            new_schema_pk = decompose_schema_pk(self.db_schema_pk, over_attributes)
            new_schema_unique = decompose_schema_unique(self.db_schema_unique, over_attributes)

            new_relation = Relation(name, schema_attributes=new_schema_attr, schema_keys=new_schema_pk,
                                    schema_unique=new_schema_unique)
        else:                           # 无 db schema -> 直接用手动属性列表
            new_relation = Relation(name, over_attributes)
        if fds is not None:             # 如有传入的 FD 则一并加入
            new_relation.fds_add(fds)
            new_relation.join_rhs_fds()
        return new_relation
