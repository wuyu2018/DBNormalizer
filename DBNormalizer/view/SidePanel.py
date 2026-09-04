# -*- coding: utf-8 -*-
# SidePanel：左侧“关系树”面板。
# 顶部是一排操作按钮（新增关系 / 新增属性），下方是一棵 Treeview：
# 每个“关系”是一个顶层节点，它的属性作为其子节点。
# 双击某关系节点时，Controller 会刷新右侧信息。
__author__ = 'Nantes'

from tkinter import *
from tkinter import ttk


class SidePanel(Frame):
    # 布局：按钮行在上，关系树在下并占满剩余空间
    def __init__(self, parent):
        Frame.__init__(self, parent)

        # 顶部的按钮条
        self.tree_buttons = RelationTreeButtons(self)
        self.tree_buttons.pack(side=TOP)

        # 下方的关系树
        self.relation_tree = RelationTree(self)
        self.relation_tree.pack(anchor=NW, expand=1, fill=BOTH)

        #self.add_relation_button = Button(self, text="Add Relation")
        #self.add_relation_button.pack(side=BOTTOM)
        #self.remove_relation_button = Button(self, text="Remove")
        #self.remove_relation_button.pack(side=BOTTOM)
        #self.tree_buttons.pack(side=BOTTOM)


class RelationTreeButtons(Frame):
    # 按钮行：“Add Relation” 与 “Add Attribute”
    def __init__(self, parent):
        Frame.__init__(self, parent)
        #        self.pack(side=BOTTOM, fill=BOTH, expand=1)
        self.frame = ttk.Frame(self)

        # 新增关系按钮（事件由 Controller 绑定）
        self.add_relation_button = ttk.Button(self, text="Add Relation")
        self.add_relation_button.pack(side=LEFT)

        # 新增属性按钮（为当前选中关系添加属性）
        self.add_attribute_button = ttk.Button(self, text='Add Attribute')
        self.add_attribute_button.pack(side=LEFT)

        #self.remove_relation_button = ttk.Button(self, text="Remove")
        #self.remove_relation_button.pack(side=LEFT)


class RelationTree(Frame):
    # 关系树：使用 ttk.Treeview，带横/纵向滚动条
    def __init__(self, parent):
        Frame.__init__(self, parent)
        #        self.pack(anchor=W, expand=1, fill=Y)
        self.parent = parent
        self.tree = ttk.Treeview(self)
        # self.tree.bind("<Double-1>", self.on_double_click)  # 双击事件在 Controller 绑定

        # 纵向/横向滚动条
        ysb = ttk.Scrollbar(self.tree, orient=VERTICAL, command=self.tree.yview)
        xsb = ttk.Scrollbar(self.tree, orient=HORIZONTAL, command=self.tree.xview)
        self.tree['yscroll'] = ysb.set
        self.tree['xscroll'] = xsb.set

        # setup column headings  设置列标题
        self.tree.heading('#0', text='Schema', anchor=NW)

        # 布局滚动条与树
        ysb.pack(side=RIGHT, fill=Y)
        xsb.pack(side=BOTTOM, fill=X)
        self.tree.pack(expand=1, fill=BOTH)
        self.rowconfigure(0, weight=1)   # 允许随窗口伸缩
        self.columnconfigure(0, weight=1)

    # 清空整棵树（重新导入时使用）
    def delete_tree(self):
        nodes = self.tree.get_children()
        for x in nodes:
            self.tree.delete(x)
