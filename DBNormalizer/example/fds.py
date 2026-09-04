# -*- coding: utf-8 -*-
# 示例：演示“函数依赖集合”的创建、打印、求闭包与右部单值化。
# 运行方式：python -m DBNormalizer.example.fds
__author__ = 'Nantes'

from DBNormalizer.model.FDependencyList import *

 # means A -> CD   # fd1 表示 A -> CD
# Instantiate 3 FDs objects:
# 实例化 3 个 FD 对象
fd1 = FDependency(['A'], ['C', 'D'])
fd2 = FDependency(['B'], ['C'])
fd3 = FDependency(['C', 'D'], ['E'])

# Instantiate an object that contains a list of FDs:
# 实例化一个 FD 集合对象（本身是 list 的子类）
fds = FDependencyList([fd2, fd3])
fds.append(fd1)  # This class inherits from list so you can use any list method!
                 # 该类继承自 list，因此可以直接使用 list 的各类方法
print(fds)

# Computes the attribute closure of AB with the FDs contained in fds
# 用 fds 中的函数依赖计算 A 的属性闭包
closure = fds.attribute_closure(['A'])
print(closure)

# Returns singleton fds:
# If AB -> ACD, then AB->A, AB->C and AB->D RETURNS A FDependencyList
# 右部单值化：把 A -> CD 拆成 A->C、A->D
singleton_from_fd_list = fds.makeRightsingleton()
print(singleton_from_fd_list)
