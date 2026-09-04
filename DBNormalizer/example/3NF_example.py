# -*- coding: utf-8 -*-
# 示例：3NF 分解(合成)演示。
# 手工给定关系 R(A,B,C,D,E) 及一组 FD，计算：最小覆盖 -> 候选键 -> 各范式违例 -> 3NF 分解提议。
# 运行方式：python -m DBNormalizer.example.3NF_example
__author__ = 'Paris'

from DBNormalizer.model.Decomp import *

N=Normalization()       # 规范化对象
D=Decomposition()       # 分解对象
RO=set(['A','B','C','D','E'])   # 关系属性全集

# 定义函数依赖
fd1 = FDependency(['A', 'B'], ['C','D'])
fd2 = FDependency(['A'], ['B'])
fd3 = FDependency(['B'], ['C'])
fd4 = FDependency(['C'], ['E'])
fd5 = FDependency(['B', 'D'], ['A'])
    # fd6 = FDependency(['C', 'D'], ['E'])
    # fd7 = FDependency(['A', 'C'], ['B'])
    # fd8 = FDependency(['A', 'C'], ['D'])
    # fd9 = FDependency(['A', 'C'], ['E'])
    # fd10 = FDependency(['C'], ['A'])
FDs = FDependencyList([fd1, fd2, fd3, fd4,fd5])   # FD 集合
minFds=FDs.MinimalCover()                          # 最小覆盖
print(minFds)
    #allKeys = FDs.candidate_keys()
allKeys=N.findCandKeys(RO,minFds,FDs)              # 候选键
print(allKeys)

# 逐条 FD 检查范式违例
for fd in minFds:
    lhs=set(fd.lh)
    rhs=set(fd.rh)

    if(N.check2NF(fd,lhs,rhs,allKeys)):
        print("2nf violation")
    if(N.check3NF(fd,lhs,rhs,allKeys)):
        print("3nf violation")
    if(N.checkBCNF(fd,lhs,rhs,allKeys)):
        print("BCNF violation")

#print(N.FDListBCNF)
#newR=D.createNewRelation(fd1)
#print(newR)
L=D.proposal3NF(RO,minFds,FDs)                      # 3NF 分解提议
print("3NF - ",L)
