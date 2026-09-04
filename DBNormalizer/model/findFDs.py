# -*- coding: utf-8 -*-
# findFDs：从数据库数据中发现函数依赖(FD)的算法。
# 基本思想：
#   对每个候选右部属性 rhs（其余属性作为可选的左部），搜索“最小”的左部集合 X，
#   使 X->rhs 在数据上成立。
# 利用关键剪枝性质：若 X->E 不成立，则 X 的任何子集 Y->E 也都不成立，
# 因此可以先从全属性试起，逐层缩小，淘汰所有不成立的候选以大幅减少检测次数。
# 判断某 FD 是否成立，是通过“行 id 的分区(partition)”完成的（见 SQLParser/Relation）。
__author__ = 'Nantes'
from itertools import chain, combinations


# 主入口：给定全部属性，逐个把每个属性当作右部，找出所有最小成立的左部。
# 返回 {rhs: [成立的最小 lhs 列表]}。
def find_fds(attributes, db_partition, test_mode=False, pk=[], uk=[]):
    attr = attributes[:]                 # 待处理属性副本
    len_attributes = attr.__len__()
    fds = {}                             # 结果：rhs -> [lhs...]
    for i in range(0, len_attributes):
        rhs = attr.pop(0)                # 轮流取一个属性作为右部
        lhs_in = attr[:]                 # 其余属性作为可选的左部池
        # pk_unique = []
        # if set(pk).issubset(set(lhs_in)):
        #     pk_unique.append(pk)
        #     lhs_in = list(set(lhs_in) - set(pk))
        # for u in uk:
        #     if set(u).issubset(set(lhs_in)):
        #         pk_unique.append(u)
        #         lhs_in = list(set(lhs_in) - set(u))
        # 找出以 rhs 为右部的最小左部集合
        lhs = find_fds_rhs(lhs_in, [rhs], db_partition, test_mode)
        fds[rhs] = lhs # + pk_unique
        attr.append(rhs)                 # 放回，保证每轮都能轮换右部
    return fds


# 找出使 X->rhs 成立的“最小”左部集合 X（X 是 lhs 的子集）。
# 算法分层：从最大集合(全属性)开始向下枚举大小减一的所有子集，
# 不成立的候选被标记(e0)并可据此剪枝其子集，成立的进入下一层(e1)。
def find_fds_rhs(lhs, rhs, db_partition, test_mode=False):
    """
    Finds all the minimal functional dependencies X->rhs with X subset of lhs. Usually lhs = U\rhs where U is the
    set of attributes in the relation. The idea of this function is to eliminate unnecessary computation using the
    fact that, if the fd X->E does not hold, then for all Y subset of X, Y->E doesn't hold either.

    db_partition doesn't play an important role in this function, it is passed to the function test_fd_db that
    determines if a given fd is satisfied by the data in db_partition.

    :param lhs: a list containing attributes in the lhs of a fd
    :param rhs: a list containing attributes in the rhs of a fd
    :param db_partition: a partition of a relation in SQL over which the dependencies are to be tested
    :return: a list with the minimal lhs that satisfy lhs->rhs
    """
    x = {tuple(lhs)}                      # 当前层要检测的候选左部集合
    e0 = set()  # set with the non-satisfied fds   记录"不成立"的候选
    e1 = set()  # set with the satisfied fds       记录"成立"的候选
    set_len = lhs.__len__()               # 当前层候选的基数(大小)
    while x.__len__() != 0 and set_len > 0:   # 一直检测到最小层为止
        level = set()  # each level tries the proper subsets of X with length len(X)-1  下一层的候选
        for subx in x:
            if test_mode:                 # 测试模式：用逻辑闭包代替数据库
                test = test_fds_test(list(subx), rhs, db_partition)
            else:                         # 正常模式：用数据库行分区判断
                test = test_fds(list(subx), rhs, db_partition)
            if not test:
                e0 = e0.union([subx])     # 该候选不成立，其所有子集也不可能成立 -> 剪枝来源
            else:
                e1 = set(remove_super_sets(list(subx), e1))  # removes redundancy in e1  去掉 e1 中已被包含的超集
                e1 = e1.union([subx])     # 记录成立候选
                level = level.union([subx])  # 成立的候选还需检查其子集能否更小
        level = set(subsets(list(level), set_len - 1))  # obtain the next level 生成下一层(大小-1的子集)
        e0 = set(subsets(list(e0), set_len - 1))  # 由不成立集合推演出的"不可能集合"
        x = prune(level, e0)              # removes the cases that are not satisfiable by means of e0 剪枝
        set_len -= 1                      # 层大小减一
    return [list(x) for x in list(e1)]    # 返回所有成立的最小左部


# 对列表 x 中每个集合，取出其大小为 k 的所有子集（用于构造下一检测层）
def subsets(x, k):
    """
    Finds the subsets of cardinality k for each element (set) of the list x
    :param x: a list of sets
    :param k: integer
    :return: list of subsets
    """
    sub_set = set()
    for i in x:
        sub_set = sub_set.union(set(combinations(i, k)))
    return list(sub_set)


# 集合差：从候选集合 x 中去掉不可能的集合 y（剪枝操作）
def prune(x, y):
    """
    Set difference
    :param x:
    :param y:
    :return:
    """
    return x - y


# 测试模式判断：若 rhs 的首属性已出现在 lhs 的闭包中，则 FD 成立
def test_fds_test(lhs, rhs, fds):
    """
    Tests if the fds lhs->rhs is satisfied in fds. This function is only for testing purposes
    :param lhs:
    :param rhs:
    :param fds:
    :return: boolean
    """
    closure = fds.attribute_closure(lhs)
    return rhs[0] in closure


# 数据库模式判断：利用行分区判定 X->rhs 是否成立。
# 成立当且仅当"凡在 lhs 各属性取值相同(落在同一块)的行，在 rhs 上也必然取值相同"。
# 即 lhs 的每个分区块必须是 rhs 某个分区块的子集。
def test_fds(lhs, rhs, relation_dict):
    lhs_partition = get_intersection(lhs, relation_dict)   # 左部的精细分区块
    rhs_partition = get_intersection(rhs, relation_dict)   # 右部的精细分区块
#    print(lhs_partition)
#    print(rhs_partition)
    x = True
    k = 0
    # 检查左部每一块是否都能嵌入右部的某一块中
    while x and k < len(lhs_partition):
        element = lhs_partition[k]
        y = False
        z = 0
        while not y and z < len(rhs_partition):
            y = set(element).issubset(set(rhs_partition[z]))  # 块属于右部某块则通过
            z += 1
        x = y
        k += 1
    return x


# def get_intersection(attributes, relation_dict):
#     res = relation_dict[attributes[0]]
#     print("--entra intersection----")
#     for i in range(1, len(attributes)):
#         x = relation_dict[attributes[i]]
#         res = [set(a).intersection(set(b)) for a in res for b in x]
#         #res = list(filter(None, [list(set(a) & set(b)) for a in res for b in x]))
#     print("--sale intersection----")
#     return res

# 对多个属性做“分区的交”(partition refinement)：
# 得到这些属性联合取值相同的最小行分组。每个块是行 id 列表；
# 两个元组属于同一块 当且仅当 它们在所有这些属性上取值一致。
def get_intersection(attributes, relation_dict):
    """
    Computes the partition refinement obtained by intersecting the partitions of the given attributes.
    Each block of a partition is a list of integer row ids, so a tuple belongs to a class of the refined
    partition if, and only if, its rows agree on every attribute.
    :param attributes: list of attribute names
    :param relation_dict: a partition of the relation: {attribute: [[row_id, ...], ...]}
    :return: a list of blocks; each block is a sorted list of row ids
    """
    if len(attributes) == 0:      # 无属性 -> 空
        return []
    res = relation_dict[attributes[0]]   # 从第一个属性的分区开始
    for i in range(1, len(attributes)):  # 逐个与其他属性分区求交
        x = relation_dict[attributes[i]]
        res_list = []
        for block in x:                 # 对每个块的每一块求交集
            block_set = set(block)
            for j in res:
                inter = block_set.intersection(j)
                if inter:               # 交集非空才保留（行在两者上都取值相同）
                    res_list.append(sorted(inter))
        res = res_list
    return res


# 从 set_of_sets 中删除所有是 sub_set 超集的元素（用于保持结果最小化）
def remove_super_sets(sub_set, set_of_sets):
    """
    Removes the elements in set_of_sets that are super sets of sub_set
    :param sub_set: a set
    :param set_of_sets: list of sets
    :return: list of sets
    """
    return [x for x in set_of_sets if not set(x).issuperset(set(sub_set))]


# print(find_fds_rhs(['essn', 'sex', 'dependent_name', 'bdate'], ['relationship'], {'sex': [[1, 3, 6, 7], [2, 4, 5]],
#                                                                                    'bdate': [[2], [6], [7], [3], [1],
#                                                                                              [4], [5]],
#                                                                                    'essn': [[1, 2, 3], [5, 6, 7], [4]],
#                                                                                    'relationship': [[3, 4, 7], [1, 6],
#                                                                                                     [2, 5]],
#                                                                                    'dependent_name': [[1, 6], [5], [2],
#                                                                                                       [7], [4], [3]]},test_mode= False))
