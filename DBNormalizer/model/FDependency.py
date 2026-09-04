# -*- coding: utf-8 -*-
# 函数依赖(FD)类：表示一条形如 LHS -> RHS 的函数依赖。
# LHS(左部)与 RHS(右部)都是"属性名"列表，例如 ['A','B'] -> ['C']。
__author__ = 'Nantes'


class FDependency:
    """
    Functional dependency class（函数依赖类）
    """
    # 构造：保存左部 lh 与右部 rh
    def __init__(self, lh, rh):
        self.lh = lh
        self.rh = rh

    # 打印成 "['A','B'] -> ['C']" 的形式，便于展示
    def __str__(self):
        """
        Printing method for the class（打印方法）
        :return: string which is printed
        """
        return str(self.lh) + ' -> ' + str(self.rh)

    # 判断两条 FD 是否等价：按集合(无序、去重)比较左右部
    def __eq__(self, other):
        """
        Returns true if self is equal to other
        :param other: an FDependency object
        :return: true or false
        """
        # Use set to compare, otherwise repeated elements are allowed
        # 用 set 比较以避免属性顺序/重复带来的误判
        return set(self.lh) == set(other.lh) and set(self.rh) == set(other.rh)
