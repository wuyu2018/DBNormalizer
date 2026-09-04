# -*- coding: utf-8 -*-
# Decomp：关系分解算法。
# 提供两种分解提议的生成：
#   - proposal3NF：基于最小覆盖的 3NF 合成（每个 FD 生成一个关系，必要时补一个“键关系”
#     以保证无损连接与依赖保持）
#   - proposalBCNF：递归地把违反 BCNF 的关系沿某条违例 FD 拆成两个子关系，
#     直到所有子关系都满足 BCNF。
# 同时提供 FDs 在子关系上的“投影”算法 projectFDs。
__author__ = 'Paris'

from DBNormalizer.model.Normalization import *

N = Normalization()   # 模块级复用一个 Normalization 实例做辅助计算

class Decomposition:
    # 初始化：保存分解得到的关系集合（元素形如 (属性集合, FDependencyList)）
    def __init__(self):
        self.List_Relation=list()
    #def combineSingleTonFD(self,MinFDs):

    # 3NF 合成分解：对最小覆盖中每个 FD 生成一个关系，然后检查候选键是否已含在
    # 某个生成的关系中；若没有，则额外增加一个“候选键关系”。
    # 输入 R：全属性集合；MinFDs：最小覆盖；Fds：原始 FD 集
    def proposal3NF(self,R,MinFDs,Fds):
        #FDs=self.combineSingleTonFD(MinFDs)
        FDs=Fds
        for fd in MinFDs:
            R1=self.createNewRelation(fd)   # 由该 FD 生成关系(取 lh 并 rh)
            #self.List_Relation.append(R1)
            F0=self.projectFDs(R,R1,MinFDs) # 把 FDs 投影到该关系上
            self.addRelation(R1,F0)         # 加入结果(会做子集去重)
        # 若候选键没有作为任何生成关系的子集出现，则补一个键关系保证无损连接
        if not self.candidateKeyChecking(R,MinFDs,FDs):
            KRs=self.createKeyRelation(R,MinFDs,FDs)  # 取第一个候选键
            Fkey=self.projectFDs(R,KRs[0],MinFDs)     # 投影 FD
            self.List_Relation.append((KRs[0],Fkey))
        return self.List_Relation

    #testing Phase
    # BCNF 分解入口：调用递归函数并返回所有子关系
    def proposalBCNF(self,R0,F0):
        accum=list()
        L=self.decomposeBCNF(R0,F0,accum)
        print("----start Recursive Call------")
        return L

    # BCNF 分解递归体：若关系 R0 违反 BCNF，取第一条违例 FD，
    # 用其左部闭包拆出一个子关系 R01，余下属性(∪左部)构成 R02，然后递归处理两者。
    def decomposeBCNF(self,R0,F0,accum):
        print("-----Start of a call")
        print("call with:",R0,F0)
        norm=Normalization()
        candKeys=norm.findCandKeys(R0,F0,F0)  # 计算当前关系的候选键
        #print(candKeys)
        # 寻找第一条违反 BCNF 的 FD
        for f in F0:
            lh=set(f.lh)
            rh=set(f.rh)
            if norm.checkBCNF(f,lh,rh,candKeys):
            #print(norm.FDListBCNF)
                break
        #print(norm.FDListBCNF)
        # 若有违例则拆分
        if not norm.FDListBCNF==[]:
            fd=norm.FDListBCNF[0]         # 取违例 FD X->Y
            #print(fd)
            X=fd.lh
            #print(X)
            xclosure=F0.attribute_closure(X)  # 求 X 的闭包
            #print(xclosure)
            R01=set(xclosure)                 # 子关系1 = X 的闭包
            #print(R01)
            R02=R0.copy()
            R02=R02.difference(R01)           # 剩余属性
            #print(R02)
            R02=R02.union(set(X))             # 再补上 X 以保持联结
            #print(R02)
            F01=self.projectFDs(R0,R01,F0)    # FD 投影到子关系1
            #print("FD:",F01)
            F02=self.projectFDs(R0,R02,F0)    # FD 投影到子关系2
            self.decomposeBCNF(R01,F01,accum) # 递归分解子关系1
            #accum.append((R01,F01))
            self.decomposeBCNF(R02,F02,accum) # 递归分解子关系2
        else:
            accum.append((R0,F0))             # 已满足 BCNF，收集该叶子关系
        print("----End of Call----")
        return accum

    # FD 投影：把 ParentFDs 投影到子关系 DecompRelation 上。
    # 方法：对子关系中每个非空子集 X 求其在父 FD 下的闭包，凡闭包里的属性 a
    # 属于子关系者，加入一条 X->a，最后对该结果取最小覆盖。
    def projectFDs(self,ParentRelation,DecompRelation,ParentFDs):
        T=FDependencyList()
        properset=N.findNonEmptySubsets(DecompRelation)   # 子关系的全部非空子集
        #print('PROPERSET = ',properset)
        for X in properset:
            xclosure=ParentFDs.attribute_closure(X)  # X 在父关系中的闭包
            #print('Xclosure',xclosure)
            for a in xclosure:
                #print("a:",a)
                if DecompRelation.__contains__(a):   # 闭包属性属于子关系才保留
                    T.append(FDependency(list(X),[a]))
        G=T.MinimalCover()                           # 投影结果再取最小覆盖
        #print("FD=",G)
        return G

    # 向结果列表加入一个新关系，同时做“子集去重”：
    # 若已有关系是新关系的子集则移除之；若新关系是已有关系的子集则放弃加入。
    def addRelation(self,R1,F):
        """ This method will check if any of the currently
            added relation is a subset of New Relation """
        #check=False;
        T=self.List_Relation.copy()
        if self.List_Relation==[]:                 # 列表为空直接加入
            self.List_Relation.append((R1,F))
        else:
            for g in T:
                if(g[0].issubset(R1)):             # 旧关系是新关系的子集 -> 删除旧关系
                    self.List_Relation.remove(g)
                #self.List_Relation.append(R1)
                else:
                    if R1.issubset(g[0]):          # 新关系是旧关系的子集 -> 丢弃新关系
                #self.List_Relation.remove(R1)
                        return 0
            self.List_Relation.append((R1,F))
        return 0

    # 用一条 FD 构造新关系的属性集合：取 lh ∪ rh
    def createNewRelation(self,nfd):
        g=list()
        g.extend(nfd.lh)
        g.extend(nfd.rh)
        return set(g)

    #N=Normalization ()
    # 求出候选键集合（3NF 补键时使用）
    def createKeyRelation(self,R,MinFDs,FDs):
        #KeyRelations=list()
        KeyRelations=N.findCandKeys(R,MinFDs,FDs)
        return KeyRelations

    # 检查当前分解结果中是否已有关系包含某个候选键
    # （若包含，则该分解是无损的，无需再补键关系）
    def candidateKeyChecking(self,R,MinFDs,FDs):
        flag=False
        keys=N.findCandKeys(R,MinFDs,FDs)
        for R2 in self.List_Relation:
            for key in keys:
                if key.issubset(R2[0]):      # 候选键被某关系包含
                    flag=True
                    return True
                else:
                    flag=False
        return flag
