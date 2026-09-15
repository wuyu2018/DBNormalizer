# -*- coding: utf-8 -*-
# ConnectionPanel：顶部的“数据库连接”面板。
# 提供数据库连接参数输入框（主机/端口/用户名/密码/数据库名）、
# “Connect DB”按钮（连接并导入模式）与“Export DDL”按钮（导出分解后的建表 SQL）。
__author__ = 'Nantes'

from tkinter import *
from tkinter import ttk

from DBNormalizer.model.ConnectionStore import connection_label

class ConnectionPanel(Frame):
    # 构造：调用 initialize 布局
    def __init__(self, parent):
        Frame.__init__(self, parent)
        self.saved_connections = []   # 历史连接列表（由 Controller 注入）
        self.initialize()   # 初始化组件与布局

    # 创建全部输入控件、按钮并放置到网格中
    def initialize(self):
        self.grid()         # 让本面板参与父级网格布局

        # 历史连接下拉框：选择一条即一键填写下方各输入框
        saved_label = Label(self, text="Saved", anchor="w")
        saved_label.grid(column=0, row=0, sticky='EW')
        self.saved_combo = ttk.Combobox(self, state="readonly")
        self.saved_combo.grid(column=1, row=0, columnspan=5, sticky='EW')
        self.saved_combo.bind("<<ComboboxSelected>>", self.select_saved_connection)

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

        # “LLM Normalize”按钮：让 LLM 迭代设计 DDL 直到满足目标范式（事件由 Controller 绑定）。
        # 单独占一整行放在显眼位置，样式与 Connect DB / Export DDL 保持一致。
        self.llm_button = Button(self, text="LLM Normalize")
        self.llm_button.grid(column=0, row=3, columnspan=6, sticky='EW', pady=(6, 2))

    # 填充历史连接下拉框
    def set_saved_connections(self, connections):
        self.saved_connections = list(connections)
        self.saved_combo["values"] = [connection_label(c) for c in self.saved_connections]
        if self.saved_connections:
            self.saved_combo.current(0)

    # 选中历史连接 -> 一键填写各输入框
    def select_saved_connection(self, event):
        idx = self.saved_combo.current()
        if idx < 0 or idx >= len(self.saved_connections):
            return
        conn = self.saved_connections[idx]
        self._fill_entry(self.host, conn.get("host", ""))
        self._fill_entry(self.port, conn.get("port", ""))
        self._fill_entry(self.username, conn.get("username", ""))
        self._fill_entry(self.password, conn.get("password", ""))
        self._fill_entry(self.database, conn.get("database", ""))

    # 用给定值覆盖某个输入框内容
    @staticmethod
    def _fill_entry(entry, value):
        entry.delete(0, END)
        entry.insert(0, value)
