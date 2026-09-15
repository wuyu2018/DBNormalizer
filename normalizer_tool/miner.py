# -*- coding: utf-8 -*-
"""函数依赖挖掘：复用现有分区算法，并加入数据质量护栏与支撑度统计。

思路与原有范式工具一致——不直接读数据，而是读"每列取值相同的行分组(分区)"，
再由 findFDs.find_fds 推导最小左部。

护栏用于剔除"样本数据导致的伪依赖"：
  * 右部只有一个分区块（该列取值恒定）=> 依赖恒真、无意义，丢弃；
  * 左部只有一个分区块（左部取值恒定）=> 依赖恒真、无意义，丢弃；
  * 平凡依赖（rhs 属于 lhs）丢弃。

同时统计每条 FD 左部的分区块数（support）：块数越少，越可能是小数据巧合。
"""
from .fds import FD
from DBNormalizer.model.SQLParser import get_attribute_partition
from DBNormalizer.model.findFDs import find_fds as _mine_fds, get_intersection

# 过滤阈值：左部至少要有这么多个不同取值分组，否则该 FD 视为无意义
MIN_LHS_GROUPS = 2


def build_partitions(engine, table, attributes):
    """对表的每个属性计算取值分区，返回 {属性名: 分区}。"""
    return {attr: get_attribute_partition(table, attr, engine) for attr in attributes}


def mine_fds(engine, table, attributes):
    """挖掘并过滤函数依赖。

    :return: (fds, partitions, support)
             fds        FD 集合
             partitions 分区明细
             support    {FD: 左部不同取值分组数}
    """
    partitions = build_partitions(engine, table, attributes)
    raw = _mine_fds(list(attributes), partitions)

    fds = set()
    support = {}
    for rhs, lhs_list in raw.items():
        if len(partitions.get(rhs, [])) <= 1:
            continue
        for lhs in lhs_list:
            if not lhs or rhs in lhs:
                continue
            lhs_groups = len(get_intersection(list(lhs), partitions))
            if lhs_groups < MIN_LHS_GROUPS:
                continue
            fd = FD(frozenset(lhs), frozenset([rhs]))
            fds.add(fd)
            support[fd] = lhs_groups
    return fds, partitions, support
