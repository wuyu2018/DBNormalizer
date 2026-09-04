# -*- coding: utf-8 -*-
# 示例：从“给定的一组 FD”中还原/验证 FD（test_mode=True，用逻辑闭包代替真实数据库）。
# 说明：给 Relation 提供 FD 集合并开启 test_mode，find_fds 会用闭包逻辑判断这些 FD 是否成立。
# 运行方式：python -m DBNormalizer.example.findFDs_example
__author__ = 'Nantes'

from DBNormalizer.model.Relation import *

# Give fds of a hypothetical database (for testing purposes):
# 给出一个假设数据库里的 FD（用于测试）
fd1 = FDependency(['A'], ['E']) # means A -> CD   # A -> E
fd2 = FDependency(['B'], ['C'])
fd3 = FDependency(['C','D'], ['E'])

fds1 = FDependencyList([fd1,fd2, fd3])
print(fds1)
# Finds the fds that satisfies the given lhs and rhs. The idea of this function is to eliminate unnecessary computation
# using th fact that, if the fd X->E does not hold, then for all Y subset of X, Y->E doesn't hold either.
# find_fds 寻找满足条件的 FD，剪枝原理：若 X->E 不成立，则 X 的任何子集 Y->E 也不成立。

# Creates a relation with only name and attributes
# 创建只有名字和属性的关系（测试用，不含数据库 schema）
relation1 = Relation('Test', ['A', 'B', 'C', 'D', 'E'])
# Find the fds in the database (for testing purposes suppose the database is one in which fds1 hold)
# 在这个测试数据库中“挖掘”FD（假设该数据库满足 fds1）
print(relation1)
relation1.find_fds(fds1, test_mode=True)   # test_mode=True：用闭包逻辑判断
print(relation1.fds)
