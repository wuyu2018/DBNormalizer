# -*- coding: utf-8 -*-
# 示例：范式(2NF/3NF/BCNF)违例判定演示。
# 手工给定一组 FD 与属性集 R，观察哪些 FD 违反了对应范式。
# 运行方式：python -m DBNormalizer.example.NF_example
__author__ = 'Paris'

from DBNormalizer.model.Normalization import *

N=Normalization()               # 规范化对象（内含各违例 FD 列表）
R=set(['A','B','C','D','E'])    # 关系的全部属性

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
allKeys=N.findCandKeys(R,minFds,FDs)               # 求候选键
print(allKeys)

# 逐条检查每条 FD 是否违反 2NF/3NF/BCNF
for fd in minFds:
    lhs=set(fd.lh)
    rhs=set(fd.rh)

    if(N.check2NF(fd,lhs,rhs,allKeys)):            # 违例 2NF
        print("2nf violation")
    if(N.check3NF(fd,lhs,rhs,allKeys)):            # 违例 3NF
        print("3nf violation")
    if(N.checkBCNF(fd,lhs,rhs,allKeys)):           # 违例 BCNF
        print("BCNF violation")

print(N.FDListBCNF)                                # 打印全部违反 BCNF 的 FD
