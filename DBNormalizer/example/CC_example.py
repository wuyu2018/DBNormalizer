# -*- coding: utf-8 -*-
# 示例：最小覆盖(Canonical Cover)计算演示。
# 对比两种调用方式：模块函数式(makeRightsingleton/removeExtraneous/removeDuplicacy)
# 与面向对象式(fdlist.MinimalCover())，二者结果相同。
# 运行方式：python -m DBNormalizer.example.CC_example
__author__ = 'Paris'

from DBNormalizer.model.mincover import *
from DBNormalizer.model.FDependencyList import *

# fd1 = FDependency(['A','B','C','D'],['E'])
# fd2 = FDependency(['A','B'],['E'])
# fd3 = FDependency(['B','C'],['E'])
# 构造一组 FD
fd1 = FDependency(['A', 'B'], ['C', 'D'])
fd2 = FDependency(['C'], ['A','D','E'])
fd3 = FDependency(['B'], ['D','E'])
fd4 = FDependency(['D'], ['E'])
fdlist = FDependencyList([fd1, fd2, fd3, fd4])

# --- 函数式（旧 mincover 模块）调用链 ---
print(makeRightsingleton(fdlist))          # 第1步：右部单值化
print(removeExtraneous(makeRightsingleton(fdlist)))   # 第2步：去多余属性
print(removeDuplicacy(removeExtraneous(makeRightsingleton(fdlist))))  # 第3步：去冗余依赖

# Example using OOP
# --- 面向对象方式（FDependencyList 内置方法）---
print(fdlist.makeRightsingleton())                     # 右部单值化
print(fdlist.makeRightsingleton().removeExtraneous())  # 再去除多余属性
print(fdlist.makeRightsingleton().removeExtraneous().removeDuplicacy())  # 再去除冗余依赖
print(fdlist.MinimalCover())                           # 一次得到最小覆盖
print(fdlist.candidate_keys())                         # 求候选键
print(fdlist.get_lhs())                                # 所有左部属性
