# -*- coding: utf-8 -*-
# mincover.py：最小覆盖(规范覆盖)的实现（旧版）。
# 注意：该文件已标注 TODO，建议删除——同样的功能现已合并进
# FDependencyList 的 MinimalCover() 方法（即 makeRightsingleton 之后
# 调用 removeExtraneous 与 removeDuplicacy）。
__author__ = 'Paris'
# TODO Remove file as now this functions are part of FunctionalDependencyList
from DBNormalizer.model.FDependencyList import *

# This file should be removed （此文件应被移除）
# 计算最小覆盖（此处返回 [Fmin]，单元素列表，属遗留写法）
def MinimalCover(F):
    Frs = makeRightsingleton(F)   # 步骤1：右部拆成单属性
    Fex =removeExtraneous(Frs)    # 步骤2：去掉多余(外在)属性
    Fmin = removeDuplicate(Fex)   # 步骤3：去掉冗余依赖
    return [Fmin]

# 右部单值化：A->BCD 拆成 A->B、A->C、A->D
def makeRightsingleton(F):
    singletonList=[]
    for fd in F:
        lhs = fd.lh
        rhs = fd.rh
        if len(rhs)>1:
            for attr in rhs:
             singletonList.append(FDependency(lhs, [attr]))
        else:
            singletonList.append(FDependency(fd.lh,fd.rh))
    return FDependencyList(singletonList)

# 判断 rhs 的首个属性是否出现在闭包列表中
def contains(closureList,rhs):
    if closureList.count(rhs[0])>=1:
        return 1
    else:
        return 0

# 计算 attr 的闭包并检查是否包含 rhs
def computeClosureNcheck(F,attr,rhs):
    if (contains(F.attribute_closure(attr),rhs))==1:
        return 1
    else:
        return 0

# 去多余(外在)属性：尝试用左部的更小子集推出同样的右部
def removeExtraneous(F):
    ExtraneousList=[]
    exFlag=0
    for fd in F:
        lhs = fd.lh
        rhs = fd.rh
        if len(lhs)>1:            # 仅当左部多属性时才可能缩减
            for attr in lhs:      # 逐个尝试移除左部属性
                if computeClosureNcheck(F,attr,rhs):  # 只剩该属性仍能推出 -> 其余为多余
                    ExtraneousList.append(FDependency([attr],rhs))
                    exFlag=1
                    break
                else:
                    exFlag=0
            if exFlag==0:         # 左部不能缩减 -> 保留原 FD
                ExtraneousList.append(FDependency(lhs,rhs))
        else:
            ExtraneousList.append(FDependency(lhs,rhs))
    return FDependencyList(ExtraneousList)

# 去冗余依赖：删除某 FD 后若其余 FD 仍能推出它，则证明该 FD 冗余
def removeDuplicacy(F):
    i=0
    while i < len(F):
        fd = F[i]
        lhs = fd.lh
        rhs = fd.rh
        temp=F.copy()
        temp.remove(fd)           # 移除当前 FD
        if computeClosureNcheck(FDependencyList( temp),lhs,rhs)==1:  # 仍能被推出
            F.remove(fd)          # 删除冗余的 FD
            continue
        else:
            i=i+1
    return F
