# -*- coding: utf-8 -*-
# FDependencyList：函数依赖集合 / 列表。
# 继承自内置 list，因此既可以直接当作列表使用，又额外提供了规范化所需的算法，
# 例如：属性闭包、最小覆盖、候选键、把右部拆成单属性、去多余属性、去冗余依赖等。
# 它是整个规范化算法的核心数据结构之一。
__author__ = 'Nantes'

from DBNormalizer.model.FDependency import *
from itertools import combinations

class FDependencyList(list):
    """
    Functional dependency class
    函数依赖(集合)类：本质上是一个 FDependency 列表，附带多种算法方法
    """
    # 打印整组 FD：每条之间用 ", " 分隔
    def __str__(self):
        """
        Printing method for the class
        :return: string which is printed
        """
        string = ''
        for i in range(self.__len__()):
            if i == 0:
                string = string + self[i].__str__()
            else:
                string = string + ', ' + self[i].__str__()
        return string

    # 按下标删除一条 FD，并返回被删除的那条（供界面删除使用）
    def remove_fd_idx(self, idx):
        removed = self.pop(idx)
        return removed

    # 属性闭包算法：反复把“左部已被闭包包含”的 FD 的右部并入闭包，
    # 直到闭包不再增长为止。这是判定蕴含、找键等所有算法的基础。
    def attribute_closure(self, attributes):
        """
        Computes the attribute closure with respect to the functional dependencies in the list
        :param attributes: list of attributes for which the closure is to be computed
        :return: list containing the attributes closure
        """
        unused = self[:]   # Copies the self (list)  待使用的 FD 副本
        closure = set(attributes)       # Stores the attribute closure. Is set because no repeated attributes allowed.
        # 闭包结果；用 set 避免重复属性
        closure_len = 0                 # Used as stopping condition  用于停止循环的旧长度
        while closure.__len__() != closure_len:  # 长度不再变化即闭包收敛
            closure_len = closure.__len__()
            unused_t = unused[:]
            for fd in unused:
                if set(fd.lh).issubset(closure):  # 左部已被闭包包含 -> 触发该 FD
                    unused_t.remove(fd)
                    closure = closure.union(set(fd.rh))  # 右部并入闭包
            unused = unused_t[:]
        return list(closure)    # Casts the set object to a list

    # 计算最小覆盖(规范覆盖) = 右部单值化 -> 去多余(外在)属性 -> 去冗余依赖
    def MinimalCover(self):
        if self==[]:
            return []
        return self.makeRightsingleton().removeExtraneous().removeDuplicacy()

    # 收集所有 FD 左部出现的属性(去重后)
    def get_lhs(self):
        attr = set()
        for fd in self:
            attr = attr.union(set(fd.lh))
        return list(attr)

    # 收集所有 FD 右部出现的属性(去重后)
    def get_rhs(self):
        attr = set()
        for fd in self:
            attr = attr.union(set(fd.rh))
        return list(attr)

    # （简化的）候选键求法：遍历左部属性组合，闭包等于全部属性即为键。
    # 注意：它与 Normalization.findCandKeys 是两套实现，正式路径使用后者。
    def candidate_keys(self):
        keys = list()
        lhs = set(self.get_lhs())
        rhs = set(self.get_rhs())
        attributes_in_fds = lhs.union(rhs)  # FD 中出现的所有属性
        for att in lhs:                     # 先试长度 1 的组合
            closure = self.attribute_closure(list(att))
            if set(closure) == attributes_in_fds:#in general it should be R  闭包覆盖全体属性即候选键
                keys.append(list(att))
        i = 2
        #while keys.__len__() == 0 and i <= lhs.__len__():
        while i <= lhs.__len__():           # 再逐级尝试更长的组合
            left = set(combinations(lhs, i))
            for k in left:
                closure = self.attribute_closure(list(k))
                if set(closure) == attributes_in_fds:
                    keys.append(list(k))
            i += 1
        return keys

    # 右部单值化：把 A->BCD 拆成 A->B、A->C、A->D 三条
    def makeRightsingleton(self):
        singletonList=[]
        for fd in self:
            lhs = fd.lh
            rhs = fd.rh
            if len(rhs)>1:                  # 右部多属性则逐属性拆分
                for attr in rhs:
                    singletonList.append(FDependency(lhs, [attr]))
            else:
                singletonList.append(FDependency(fd.lh,fd.rh))
        return FDependencyList(singletonList)

    # 辅助：判断给定属性组合 attr 的闭包中是否包含 rhs 首属性
    def computeClosureNcheck(self, attr, rhs):
        def contains(closureList, rhs):
            if closureList.count(rhs[0]) >= 1:  # 闭包里出现过该属性
                return 1
            else:
                return 0
        if (contains(self.attribute_closure(attr),rhs))==1:
            return 1
        else:
            return 0

    # 求集合 S 的所有非空子集
    def findNonEmptySubsets(self,S):
        subs = [set(j) for i in range(len(S)) for j in list(combinations(S, i + 1))]
        return subs

    # 去多余(外在)属性：对左部多于一个属性的 FD，尝试用更小的左部子集推出同一右部
    def removeExtraneous(self):
        ExtraneousList=[]
        exFlag=0
        for fd in self:
            lhs = fd.lh
            rhs = fd.rh
            if len(lhs)>1:                  # 左部有多个属性才需要缩减
                # L = 左部的全部非空子集
                L=[list(j) for i in range(len(lhs)) for j in list(combinations(set(lhs),i+1))]
                for attr in L:
                    if self.computeClosureNcheck(attr,rhs):  # 该子集闭包已能推出 rhs -> 存在冗余属性
                        ExtraneousList.append(FDependency(attr,rhs))
                        exFlag=1
                        break
                    else:
                        exFlag=0
                if exFlag==0:               # 没有任何子集能推出，则保留原 FD
                    ExtraneousList.append(FDependency(lhs,rhs))
            else:
                ExtraneousList.append(FDependency(lhs,rhs))
        return FDependencyList(ExtraneousList)

    # 去冗余依赖：若删除某条 FD 后，用剩余 FD 仍能推出它（闭包校验），则把它删掉
    def removeDuplicacy(self):
        i=0
        while i < len(self):
            fd = self[i]
            lhs = fd.lh
            rhs = fd.rh
            temp=self.copy()                # 暂存"去掉当前 FD"的列表
            temp.remove(fd)
            if FDependencyList(temp).computeClosureNcheck(lhs,rhs) == 1:  # 其余 FD 已能推出它
                self.remove(fd)             # 该 FD 是冗余的，删掉
                continue                    # 删除后下标不前进，继续检查
            else:
                i = i+1
        return self
