# -*- coding: utf-8 -*-
# RightPanel：右侧信息面板。自上而下分四块：
#   frame_one   ：显示表名与范式
#   frame_two   ：含 FDs / Minimal Cover / NF Violations / Table Information 四个标签页
#   frame_three ：候选键与属性闭包（含“Attribute Closure”按钮）
#   frame_four  ：3NF / BCNF 两个规范化按钮
# 本文件只负责界面布局，不含业务逻辑。
__author__ = 'Nantes'

from tkinter import *
from tkinter.messagebox import *
from tkinter.filedialog import *
from tkinter.ttk import *
from tkinter import ttk
from tkinter import font


class RightPanel(Frame):
    # 把四个子面板自上而下叠加
    def __init__(self,parent):
        Frame.__init__(self,parent)
        #self.pack(anchor=N, expand=1, fill=BOTH)

        # 区块一：关系名与范式显示
        self.frame_one_t = frame_one(self)
        #self.frame_one_t.grid(column=1,row=2, sticky=(W,E))
        self.frame_one_t.pack(anchor=NW, expand=0, fill=X)

        # 区块二：FD 与表信息（含多个标签页）
        self.frame_two_t = frame_two(self)
        #self.frame_two_t.grid(column=1,row=3, sticky=(W,E))
        self.frame_two_t.pack(anchor=NW, expand=1, fill=BOTH)

        # 区块三：候选键与属性闭包
        self.frame_three_t = frame_three(self)
        #self.frame_three_t.grid(column=1,row=3, sticky=(W,E))
        self.frame_three_t.pack(anchor=NW, expand=0, fill=X)

        # 区块四：规范化(3NF/BCNF)按钮
        self.frame_four_t = frame_four(self)
        #self.frame_four_t.grid(column=1,row=3, sticky=(W,E))
        self.frame_four_t.pack(anchor=NW, expand=0, fill=X)

class frame_one(Frame):
    # “表名与范式”区域
    def __init__(self,parent):
        LabelFrame.__init__(self,parent, text="Table Name and Normal Form")
        #self.pack(anchor=NW, expand=1, fill=X)
        self.subFrame1 = subFrame(self)
        self.subFrame1.pack(anchor=NW, expand=0, fill=X)


class subFrame(Frame):
    # 显示当前关系名与范式的两个标签
    def __init__(self,parent):
        Frame.__init__(self, parent)
        #self.pack(anchor=NW, expand=1, fill=X)
        # table_name = StringVar()
        # table_name_entry = ttk.Entry(self, width=7, textvariable=table_name)
        # table_name_entry.grid(column=1, row=1, sticky=(W, E))
        fonts = font.Font(size=12, weight='bold')   # 加粗大字体

        # “关系名”标签（值由 Controller 写入 var_name）
        self.table_label = Label(self, text="Relation Name: ")
        self.table_label.pack(anchor=NW)
        self.var_name = StringVar()
        self.table_name = ttk.Label(self, textvariable=self.var_name, font=fonts)
        self.table_name.pack(anchor=NW)

        # “范式”标签（值由 Controller 写入 var_nf）
        self.nf_label = Label(self, text="Normal Form: ")
        self.nf_label.pack(anchor=NW)
        self.var_nf = StringVar()
        self.normal_form = ttk.Label(self, textvariable=self.var_nf, font=fonts)
        self.normal_form.pack(anchor=NW)

        #self.table_label.grid(column=0, row=0)
        #self.nf_label.grid(column=0, row=1)
        #self.table_name.grid(column=1, row=0)
        #self.normal_form.grid(column=1, row=1)

class TableName(Frame):
    # (遗留/备用)显示表名的简单控件
    def __init__(self, parent):
        Frame.__init__(self, parent)
        self.table_name_entry = ttk.Label(self, text="")
        #self.table_name_entry.grid(column=1, row=1, sticky=(NW))

class NormalForm(Frame):
    # (遗留/备用)显示范式的简单控件
    def __init__(self, parent):
        Frame.__init__(self,parent)
        self.normal_form_entry = ttk.Label(self, text="")
        #self.normal_form_entry.grid(column=1, row=1, sticky=(NW))

class frame_two(Frame):
    # “FD 与表信息”大区块：内含一个多标签笔记本(FDS_notebook)
    def __init__(self,parent):
        LabelFrame.__init__(self,parent, text="FDs and Table Information", width=100)
        #self.pack(anchor=N, expand=1, fill=BOTH)
        self.subFrame2 = subFrame2(self)
        self.subFrame2.pack(anchor=N, expand=1, fill=BOTH)

class subFrame2(Frame):
    # 容纳 FDS_notebook 的容器
    def __init__(self,parent):
        Frame.__init__(self, parent)
        #self.pack(anchor=NW, expand=1, fill=BOTH)
        self.fds_notebook = FDS_notebook(self)
        self.fds_notebook.pack(anchor=N, expand=1, fill=BOTH)


class FDS_notebook(Frame):
    # 笔记本控件，四个标签页：
    #   FDs / Minimal Cover / NF Violations / Table Information
    def __init__(self,parent):
        Frame.__init__(self, parent)
        #self.pack(anchor=N, expand=1, fill=BOTH)
        self.n = ttk.Notebook(self)
        self.tab1 = FDS_tab1(None)         # 标签1：用户编辑的 FD 列表
        self.n.add(self.tab1, text='FDs', sticky=N+E+S+W)
        self.tab2 = FDS_tab2(None)         # 标签2：最小覆盖
        self.n.add(self.tab2, text='Minimal Cover', sticky=N+E+S+W)
        self.tab3=FDS_tab3(None)           # 标签3：范式违例
        self.n.add(self.tab3, text='NF Violations', sticky=N+E+S+W)
        self.tab4=FDS_tab4(None)           # 标签4：表信息(来自数据库 schema)
        self.n.add(self.tab4, text='Table Information', sticky=N+E+S+W)
        #self.n.grid(sticky=N)
        self.n.pack(expand=1, fill=BOTH)

class FDS_tab1(Frame):
    # “FDs”标签页：显示/编辑 FD 的列表 + 底部按钮(Remove/Add/Save)
    def __init__(self, parent):
        Frame.__init__(self,parent)
        #self.pack(anchor=N, expand=1, fill=BOTH)
        self.fds_table = Listbox(self)     # FD 列表框
        self.fds_table.pack(expand=1, fill=BOTH)
        self.fds_buttons_1 = FDS_tab1_buttons(self)   # 操作按钮
        self.fds_buttons_1.pack(fill=BOTH, side=BOTTOM)

        # 滚动条
        ysb = ttk.Scrollbar(self.fds_table, orient=VERTICAL, command=self.fds_table.yview)
        xsb = ttk.Scrollbar(self.fds_table,orient=HORIZONTAL, command=self.fds_table.xview)
        self.fds_table['yscroll'] = ysb.set
        self.fds_table['xscroll'] = xsb.set
        self.fds_table.pack(expand=1, fill=BOTH)
        ysb.pack(side=RIGHT, fill=Y)
        xsb.pack(side=BOTTOM, fill=X)


class FDS_tab1_buttons(Frame):
    # FD 列表下方的操作按钮：Remove / Add / Save
    def __init__(self,parent):
        Frame.__init__(self,parent)
        self.tab1_frame = ttk.Frame(self)
        self.tab1_frame.pack(side= BOTTOM)

        self.button_remove = ttk.Button(self.tab1_frame, text="Remove")  # 删除所选 FD
        self.button_remove.pack(side=LEFT)
        self.button_add = ttk.Button(self.tab1_frame, text="Add")        # 新增 FD
        self.button_add.pack(side=LEFT)
        self.button_save = ttk.Button(self.tab1_frame, text="Save")      # 保存(重算指标)
        self.button_save.pack(side=LEFT)


class FDS_tab2(Frame):
    # “Minimal Cover”标签页：显示最小覆盖(规范覆盖)
    def __init__(self, parent):
        Frame.__init__(self,parent)
        #self.pack(anchor=N, expand=1, fill=BOTH)
        self.cover_table = Listbox(self)   # 覆盖列表
        #self.cover_table.pack(expand=1, fill=BOTH)
        # 滚动条
        ysb = ttk.Scrollbar(self.cover_table, orient=VERTICAL, command=self.cover_table.yview)
        xsb = ttk.Scrollbar(self.cover_table,orient=HORIZONTAL, command=self.cover_table.xview)
        self.cover_table['yscroll'] = ysb.set
        self.cover_table['xscroll'] = xsb.set
        self.cover_table.pack(expand=1, fill=BOTH)
        ysb.pack(side=RIGHT, fill=Y)
        xsb.pack(side=BOTTOM, fill=X)


class FDS_tab3(Frame):
    # “NF Violations”标签页：文本区域展示 2NF/3NF/BCNF 违例 FD
    def __init__(self, parent):
        Frame.__init__(self,parent)
        #self.pack(anchor=N, expand=1, fill=BOTH)
        self.text_box = Text(self, height=10)   # 多行文本
        self.text_box.pack(expand=1, fill=BOTH)
        ysb = ttk.Scrollbar(self.text_box, orient=VERTICAL, command=self.text_box.yview)
        self.text_box['yscroll'] = ysb.set
        ysb.pack(side=RIGHT, fill=Y)


class FDS_tab4(Frame):
    # “Table Information”标签页：文本区域展示数据库中的表结构信息
    def __init__(self, parent):
        Frame.__init__(self,parent)
        #self.pack(anchor=N, expand=1, fill=BOTH)
        self.text_box = Text(self, height=10)
        self.text_box.pack(expand=1, fill=BOTH)
        ysb = ttk.Scrollbar(self.text_box, orient=VERTICAL, command=self.text_box.yview)
        self.text_box['yscroll'] = ysb.set
        ysb.pack(side=RIGHT, fill=Y)


class Table_info_label(Frame):
    # (遗留/备用)表信息标题标签
    def __init__(self, parent):
        Label.__init__(self, parent, text= "table name, attribute, etc")
#        table_name = StringVar()
#        table_name_entry = ttk.Entry(self,  textvariable=table_name)

class frame_three(Frame):
    # “候选键与属性闭包”大区块：含候选键列表、属性闭包列表、计算按钮
    def __init__(self,parent):
        LabelFrame.__init__(self,parent, text="Candidate Keys and attribute closure")
        #self.pack(anchor=N, expand=1, fill=BOTH)
        self.subFrame3 = subFrame3(self)          # 候选键列表
        self.subFrame3.pack(side=LEFT, expand=1, fill=X)
        self.subFrame3_2 = subFrame3_2(self)      # 属性闭包列表
        self.subFrame3_2.pack(side=LEFT, expand=1, fill=X)
        self.attributeButton = attribute_closure_button(self)  # 闭包计算按钮
        self.attributeButton.pack(side=LEFT, expand=1,fill=X)


class subFrame3(Frame):
    # “候选键”列表区域
    def __init__(self,parent):
        LabelFrame.__init__(self, parent, text="Candidate Keys")
        #self.pack(anchor=NW, expand=1, fill=BOTH)
        self.keys_list = Listbox(self, height=7)  # 候选键列表
        # 滚动条
        ysb = ttk.Scrollbar(orient=VERTICAL, command=self.keys_list.yview)
        xsb = ttk.Scrollbar(orient=HORIZONTAL, command=self.keys_list.xview)
        self.keys_list['yscroll'] = ysb.set
        self.keys_list['xscroll'] = xsb.set
        self.keys_list.grid(in_=self, row=0, column=0, sticky=NSEW)
        ysb.grid(in_=self, row=0, column=1, sticky=NS)
        xsb.grid(in_=self, row=1, column=0, sticky=EW)
        #self.keys_list.pack(anchor=NW, fill=X)


class subFrame3_2(Frame):
    # “属性闭包”列表区域
    def __init__(self,parent):
        LabelFrame.__init__(self,parent, text="Attribute Closure")
        self.attr_closure_list = Listbox(self, height=7)  # 闭包结果列表
        # 滚动条
        ysb = ttk.Scrollbar(orient=VERTICAL, command=self.attr_closure_list.yview)
        xsb = ttk.Scrollbar(orient=HORIZONTAL, command=self.attr_closure_list.xview)
        self.attr_closure_list['yscroll'] = ysb.set
        self.attr_closure_list['xscroll'] = xsb.set
        self.attr_closure_list.grid(in_=self, row=0, column=0, sticky=NSEW)
        ysb.grid(in_=self, row=0, column=1, sticky=NS)
        xsb.grid(in_=self, row=1, column=0, sticky=EW)


class attribute_closure_button(Frame):
    # “Attribute Closure”按钮（点击弹窗输入属性并计算闭包）
    def __init__(self,parent):
        Frame.__init__(self,parent)
        self.button_attribute_closure = ttk.Button(self, text="Attribute Closure")
        self.button_attribute_closure.pack(side=LEFT)


class frame_four(Frame):
    # 底部“规范化按钮”大区块
    def __init__(self,parent):
        LabelFrame.__init__(self,parent)
        #self.pack(anchor=N, expand=1, fill=BOTH)
        self.subFrame4 = subFrame4(self)
        self.subFrame4.pack(anchor=NW, expand=0)


class subFrame4(Frame):
    # 容纳按钮帧的容器
    def __init__(self,parent):
        Frame.__init__(self, parent)
        #self.pack(anchor=NW, expand=1, fill=BOTH)
        self.buttons_frame = ButtonsFrame(self)
        self.buttons_frame.pack(anchor=S)


class ButtonsFrame(Frame):
    # “3NF Normalization”与“BCNF Normalization”两个按钮
    def __init__(self, parent):
        Frame.__init__(self,parent)
        self.button_normalization = ttk.Button(self, text="3NF Normalization")  # 3NF 分解
        self.button_normalization.pack(side=LEFT)
        self.button_bcnf = ttk.Button(self, text="BCNF Normalization")          # BCNF 分解
        self.button_bcnf.pack(side=LEFT)
