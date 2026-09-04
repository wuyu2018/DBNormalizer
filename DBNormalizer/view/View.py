# -*- coding: utf-8 -*-
# View：视图层的总入口，负责把三个主面板组合到主窗口里：
#   - 顶部：数据库连接面板 ConnectionPanel
#   - 左侧：关系树面板 SidePanel
#   - 右侧：FD/规范化信息面板 RightPanel
# 它本身不含业务逻辑，只负责布局；事件处理都由 Controller 绑定。
__author__ = 'Nantes'

from DBNormalizer.view.ConnectionPannel import *
from DBNormalizer.view.SidePanel import *
from DBNormalizer.view.RightPanel import *
from DBNormalizer.view.FD_topWindow import *
from DBNormalizer.view.AC_topWindow import *
from DBNormalizer.view.AddRelAttribute import *


class View():
    # 创建并布局三个面板
    def __init__(self, parent):
        # 顶部连接面板，横向铺满
        self.connection_panel = ConnectionPanel(parent)
        self.connection_panel.pack(anchor=NW, fill=X)

        # 左侧关系树面板，纵向可伸展
        self.side_panel = SidePanel(parent)
        self.side_panel.pack(side=LEFT, anchor=NW, expand=1, fill=BOTH)

        # 右侧信息面板，纵向可伸展
        self.right_panel = RightPanel(parent)
        self.right_panel.pack(side=LEFT, anchor=NW, expand=1, fill=BOTH)

        #self.connection_panel.grid(row=0)
        #self.side_panel.grid(column=0, row=1)
        #self.right_panel.grid(column=1, row=1)
