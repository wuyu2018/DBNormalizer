# -*- coding: utf-8 -*-
# ConnectionPanel：顶部的“数据库连接”面板。
# 提供数据库连接参数输入框（主机/端口/用户名/密码/数据库名）、
# “Connect DB”按钮（连接并导入模式）与“Export DDL”按钮（导出分解后的建表 SQL）。
__author__ = 'Nantes'

from tkinter import *
from tkinter import ttk

class ConnectionPanel(Frame):
    # 构造：调用 initialize 布局
    def __init__(self, parent):
        Frame.__init__(self, parent)
        self.initialize()   # 初始化组件与布局

    # 创建全部输入控件、按钮并放置到网格中
    def initialize(self):
        self.grid()         # 让本面板参与父级网格布局

        # 定义各输入框前的标签
        host_label = Label(self, text="Host", anchor="w")
        port_label = Label(self, text="Port", anchor="w")
        username_label = Label(self, text="Username", anchor="w")
        password_label = Label(self, text="Password", anchor="w")
        database_label = Label(self, text="Database", anchor="w")

        # 创建 5 个文本输入框（值由 Controller 读取）
        self.host = Entry(self)
        self.port = Entry(self)
        self.username = Entry(self)
        self.password= Entry(self)
        self.database = Entry(self)

        # 放置输入框
        self.host.grid(column=1,row=1,sticky='EW')
        self.port.grid(column=1,row=2,sticky='EW')
        self.username.grid(column=3,row=1,sticky='EW')
        self.password.grid(column=3,row=2,sticky='EW')
        self.database.grid(column=5,row=1,sticky='EW')

        # 放置标签
        host_label.grid(column=0,row=1,sticky='EW')
        port_label.grid(column=0,row=2,sticky='EW')
        username_label.grid(column=2,row=1,sticky='EW')
        password_label.grid(column=2,row=2,sticky='EW')
        database_label.grid(column=4,row=1,sticky='EW')

        # “连接数据库”按钮（点击事件由 Controller 绑定）
        self.connect_button = Button(self, text="Connect DB")
        #self.cancel_button = Button(self,text="Cancel", command=self.destroy)
        self.connect_button.grid(column=4,row=2)
        #self.cancel_button.grid(column=0,row=6)

        # “导出 DDL”按钮：把分解结果输出成 SQL 脚本
        self.sql_output_button = Button(self, text="Export DDL")
        self.sql_output_button.grid(column=5,row=2,sticky='EW')
