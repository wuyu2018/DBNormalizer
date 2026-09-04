# -*- coding: utf-8 -*-
# 示例：BCNF 分解演示。
# 手工给定关系 R(A,B,C,D,E) 与一组 FD，计算最小覆盖、候选键，并调用 proposalBCNF
# 递归分解，得到满足 BCNF 的子关系（属性集合 + 投影 FD）。
# 运行方式：python -m DBNormalizer.example.BCNF_example
__author__ ='Paris'


from DBNormalizer.model.Decomp import *

N=Normalization()       # 规范化对象
D=Decomposition()       # 分解对象
RO=set(['A','B','C','D','E'])   # 关系属性全集

# 定义函数依赖
fd1 = FDependency(['A','B'],['C'])
fd2 = FDependency(['B'],['D'])
fd3 = FDependency(['A','B','E'],['C','D'])
fd4 = FDependency(['C','D'],['E'])
fd5 = FDependency(['C','E'],['A'])
# fd1 = FDependency(['A', 'B'], ['C','D'])
# fd2 = FDependency(['A'], ['B'])
# fd3 = FDependency(['B'], ['C'])
# fd4 = FDependency(['C'], ['E'])
# fd5 = FDependency(['B', 'D'], ['A'])
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

# for fd in minFds:
#     lhs=set(fd.lh)
#     rhs=set(fd.rh)
#
#     if(N.check2NF(fd,lhs,rhs,allKeys)):
#         print("2nf violation")
#     if(N.check3NF(fd,lhs,rhs,allKeys)):
#         print("3nf violation")
#     if(N.checkBCNF(fd,lhs,rhs,allKeys)):
#         print("BCNF violation")

print(N.FDListBCNF)                                # 打印违反 BCNF 的 FD
L=D.proposalBCNF(RO,minFds)                        # 递归执行 BCNF 分解
for l in L:
    print(l[0])                                    # 子关系的属性集合
    print(l[1])                                    # 子关系上的投影 FD
    print("\n")
