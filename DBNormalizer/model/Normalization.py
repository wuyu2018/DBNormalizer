# -*- coding: utf-8 -*-
# Normalization：规范化相关算法的实现。
# 提供：
#   - 候选键求解 findCandKeys（把属性分成必要/无用/有用三类后组合枚举）
#   - 2NF/3NF/BCNF 违例判定 check2NF / check3NF / checkBCNF
#   - 若干集合辅助方法（非空子集、属性分类、子集判定等）
# 该类的实例会保存违例 FD 列表（FDList2NF/FDList3NF/FDListBCNF），
# 供 Relation.set_normalization 判断关系当前所处的范式。
__author__ = 'Paris'

from itertools import combinations
from DBNormalizer.model.mincover import *
from DBNormalizer.model.FDependencyList import *

class Normalization:
#lhs is a set of LHS attributes            lhs 为左部属性集合
#candKeys is a set of all candidate Keys {{a,b},{bcd}}  全部候选键
#key is boolean to store if lhs is key or not

    # 初始化三个违例列表
    def __init__(self):
        self.FDList2NF=FDependencyList()    # 违反 2NF 的 FD
        self.FDList3NF=FDependencyList()    # 违反 3NF 的 FD
        self.FDListBCNF=FDependencyList()   # 违反 BCNF 的 FD
        self.FDListNoNF=FDependencyList()   # 违反 1NF(保留备用)

    # 判断 lhs 是否正好等于某个候选键
    def isKey(self,lhs, candKeys):
        key = False
        if (candKeys.__contains__(lhs)):    # 是候选键则 True
            key = True
        return key

    #rhs is set
    #singleton is boolean variable
    # 判断 rhs 是否单属性（NF 检查中常要求右部为单属性）
    def isSingleton(self,rhs):
        singleTon = False
        l =rhs.__len__()
        if (l == 1):
            singleTon = True
        return singleTon

    #attr is a single Attribute
    #candKeys is set of candidate keys
    #prime is boolean variable
    # 判断某个(属性集合)是否为非主属性：
    # 若它不是任何候选键的子集，则属于非主属性（返回 True）
    def isNonPrime(self,attr, candKeys):
            """ check if attr is a non prime attribute
               param attr: Attribute of a realtion
               param candKeys: list of Candidate Keys
               retutn boolean: True of non Prime else false"""

            prime = False
            for key in candKeys:
                if (attr.issubset(key)):    # 被某候选键包含 -> 主属性
                    prime = True
                    print("Prime:",attr)
                    break
            noPrime=not prime
            print(noPrime)
            return noPrime

    #lhs is set of LHS attributes
    #key is a single key in set format extracted from allKeys
    #propersubset is boolean variable
    # 判断 lhs 是否为 key 的真子集（2NF 检查用：部分依赖即 lhs 真包含于候选键）
    def isProperSubset(self,lhs, key):
        propersubset = False
        if (lhs.issubset(key) and not key.issubset(lhs)):
            propersubset = True
        return propersubset

    #S is set
    #subs is a list of all the non empty subsets of S subs=[{a},{b},{a,b}]
    # 返回集合 S 的全部非空子集
    def findNonEmptySubsets(self,S):
        subs = [set(j) for i in range(len(S)) for j in list(combinations(S, i + 1))]
        return subs

    #minFDs is the list of Minimum Cover of R over FDs
    #LRset=[{LHSs},{RHSs}]
    #L={LHSs}
    #R={RHSs}
    # 统计全部 FD 中出现的左部属性集合 L 与右部属性集合 R，返回 [L, R]
    def getLnRSet(self,minFDs):
        LRset = list()
        L = []
        R = []
        for fd in minFDs:
            L.extend(fd.lh)
            R.extend(fd.rh)
        LRset.append(set(L))
        LRset.append(set(R))
        return LRset

    #R={all the attributes}  R 为全集
    #S=[{LHSs},{RHSs}]
    #necessary is the necessary attributes
    # 求"必要属性"：出现在左部、或完全不出现在任何 FD 中的属性
    # （这些属性一定属于每个候选键）
    def getNecessaryAttribute(self,R, minFDs):
        S = Normalization.getLnRSet(self,minFDs)
        necessary = R.difference(S[0].union(S[1]))  # 从未出现在 FD 中的属性
        necessary = necessary.union(S[0].difference(S[1]))  # 只出现在左部的属性
        return necessary

    #R={all the attributes}
    #S=[{LHSs},{RHSs}]
    #useless is the useless attributes
    # 求"无用属性"：只出现在右部、从未出现在左部的属性
    # （这些属性一定不属于任何候选键）
    def getUseLessAttribute(self,R, minFDs):
        S = Normalization.getLnRSet(self,minFDs)
        useless = S[1].difference(S[0])
        return useless

    #X is the set of Necessary Attributes
    #Y is the set Useless Attributes
    #M is the set of neither Necessary nor Useless
    # 求"有用(中性)属性"：既非必要也非无用，可能属于也可能不属于键
    def getUsefulAttribute(self,R, X, Y):
        #X=getNecessaryAttribute(R,minFDs)
        #Y=getUseLessAttribute(R,minFDs)
        M = R.difference(X.union(Y))
        return M

    #X is set to be added to each elements(sets) of L
    #L is set of sets
    # 把集合 X 并入 L 中每一个集合
    def addedL(self,L, X):
        L1 = list()
        for Z in L:
            L1.append(Z.union(X))
        return L1

    #candKeys is the List of Sets of candidate Key
    #zclosure is set that contains closure of Z
    # 求解全部候选键：
    # 原理——任何候选键 = 必要属性 X ∪ (有用属性 M 的某个组合)，
    # 然后对候选组合 Z 求闭包，若等于全属性 R 则为候选键。
    def findCandKeys(self,R, minFDs,FDs):
        candKeys = list()
        X = self.getNecessaryAttribute(R, minFDs)   # 必要属性
        #print(X)
        Y = self.getUseLessAttribute(R, minFDs)     # 无用属性
        #print(Y)
        M = self.getUsefulAttribute(R,X, Y)         # 中性属性
        #print(M)
        L = self.findNonEmptySubsets(M)             # 中性属性的全部非空子集
        if(X!=set()):
            xclosure =set(FDs.attribute_closure(X)) # 只靠必要属性看能否覆盖全关系
            #print(xclosure)
            if (xclosure == R):
                #print("True")
                candKeys.append(X)                  # 必要属性本身就是候选键
                #print(candKeys)
            else:
                L = self.addedL(L, X)               # 否则每个候选组合都要拼上 X
        #L = self.findNonEmptySubsets(M)
        #L = self.addedL(L, X)
        #print(L)
        #i = 0
        while L != []:                              # 广度优先地逐个试候选组合
            #i = i + 1
            Z = L[0]
            del L[0]
            zclosure = set(FDs.attribute_closure(Z))  # 求候选组合的闭包
            if (zclosure == R):                     # 能覆盖全关系 -> 候选键
                #candKeys=self.addNewKey(Z,candKeys)
                candKeys.append(Z)
                #candKeys=self.removeSuperSet(Z,candKeys)
                L=self.removeSuperSet(Z, L)         # 它的超集不可能再是键，剪枝
        return candKeys

    # 从候选集合 L 中删除所有含 Z 的超集（因为若 Z 是键，超集必不是最小键）
    def removeSuperSet(self,Z, L):
        L1 = L.copy()
        for l in L1:
            if (Z.issubset(l)):
                L.remove(l)
        return L

    # 计算闭包并转为 set（静态工具，未用到 self）
    def findClosure(Fds,attr):
        closure=Fds.attribute_closure(attr)
        return set(closure)

    #keys=[set(l) for l in allKeys]
    #print(keys)
    #violation2nf variable keeps the state of violation [true or false]
    #isSigleton(fd) checks if given fd is singleton (rightside with single attribute)
    #candKeys is list of candidate Keys computed beforehand
    #isProperSubset(lhs, key) checks if lhs is a proper subset of key.
    #nonPrime(rhs) checks if rhs is a non Prime attribute
    # 检查 2NF 违例：存在"非主属性对候选键的部分依赖"即违例。
    # 即：右部单属性、非主，且左部是某候选键的真子集。
    def check2NF(self,fd, lhs, rhs, candKeys):
        violation2NF = False
        if (self.isSingleton(rhs)):                 # 右部须为单属性
            for key in candKeys:
                if (self.isProperSubset(lhs, key)): # lhs 真包含于候选键 -> 部分依赖
                    if (self.isNonPrime(rhs,candKeys)):  # 且右部为非主属性
                        violation2NF = True
                        self.FDList2NF.append(fd)   # 记录违例 FD
                        break
        return violation2NF

    #iskey(lhs,candKeys) test if lhs is key
    #toAttributeList(rhs) get the all the attributes in right Hand side as a List
    # 检查 3NF 违例：左部不是超键，且右部存在非主属性 -> 违例(传递依赖/非直接依赖)
    def check3NF(self,fd, lhs, rhs, candKeys):
            violation3NF = False
            if (self.isKey(lhs, candKeys)):         # lhs 是键 -> 合法
                violation3NF = False
            else:
                for attr in rhs:
                    if (self.isNonPrime(set([attr]), candKeys)):  # 右部含非主属性
                        violation3NF = True
                        print("3nf",fd)
                        self.FDList3NF.append(fd)
                        break
            return violation3NF

    #lhs and rhs are set of LHS and RHS attributes respectively
    # 检查 BCNF 违例：凡左部不是(超)键即违例（比 3NF 更严格）
    def checkBCNF(self,fd, lhs, rhs, candKeys):
        violationBCNF = False
        if (not self.isKey(lhs, candKeys)):
            violationBCNF = True
            self.FDListBCNF.append(fd)
        return violationBCNF
