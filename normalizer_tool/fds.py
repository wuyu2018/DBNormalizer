# -*- coding: utf-8 -*-
"""函数依赖(FD)的轻量表示与互转工具。

本模块用一个不可变对象 FD 表示一条依赖 X -> Y，
并提供与现有项目 FDependency / FDependencyList 的双向转换，
以便复用 DBNormalizer.model.Decomp 的分解算法。
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class FD:
    """一条函数依赖：lhs -> rhs，左右部均为属性名的 frozenset。"""

    lhs: frozenset
    rhs: frozenset

    def __str__(self):
        return fd_to_str(self)


def _attrs_str(attrs):
    return ', '.join(sorted(attrs))


def fd_to_str(fd):
    """格式化为 'a, b -> c' 形式（属性名按字典序，结果确定）。"""
    return _attrs_str(fd.lhs) + ' -> ' + _attrs_str(fd.rhs)


def parse_fd(text):
    """解析 'a, b -> c' 形式的字符串为 FD。"""
    left, right = text.split('->')
    lhs = frozenset(x.strip() for x in left.split(',') if x.strip())
    rhs = frozenset(x.strip() for x in right.split(',') if x.strip())
    return FD(lhs, rhs)


def sort_key(fd):
    """用于稳定排序的键。"""
    return (len(fd.lhs), sorted(fd.lhs), len(fd.rhs), sorted(fd.rhs))


def from_miner_result(raw):
    """把 find_fds 的 {rhs: [lhs, ...]} 结果转成 FD 集合（未加护栏）。"""
    fds = set()
    for rhs, lhs_list in raw.items():
        for lhs in lhs_list:
            fds.add(FD(frozenset(lhs), frozenset([rhs])))
    return fds


def to_legacy(fds):
    """转成现有项目的 FDependencyList，供 Decomp 等复用。"""
    from DBNormalizer.model.FDependencyList import FDependencyList
    from DBNormalizer.model.FDependency import FDependency

    lst = FDependencyList()
    for fd in sorted(fds, key=sort_key):
        lst.append(FDependency(sorted(fd.lhs), sorted(fd.rhs)))
    return lst


def from_legacy(fd_list):
    """从 FDependencyList（或任意含 lh/rh 的序列）转成 FD 集合。"""
    fds = set()
    for fd in fd_list:
        fds.add(FD(frozenset(fd.lh), frozenset(fd.rh)))
    return fds
