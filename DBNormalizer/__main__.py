# -*- coding: utf-8 -*-
# 程序入口模块。
# 通过 `python -m DBNormalizer` 启动时执行：创建 Controller（负责把 Model 与 View 组装起来），
# 然后调用 run() 进入 Tkinter 主事件循环。
__author__ = 'humberto'

from DBNormalizer.controller.Controller import *

if __name__ == '__main__':
    c = Controller()  # 初始化模型、视图，并绑定各种按钮/树节点的事件
    c.run()           # 启动图形界面主循环，直到窗口被关闭
