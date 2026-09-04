# -*- coding: utf-8 -*-
# 控制器层：充当“视图(View)”与“模型(Model)”之间的桥梁。
# 负责创建界面、把界面上的按钮/树节点事件绑定到对应处理函数，
# 事件触发后调用模型层进行计算，再把结果回填到界面控件上显示。
__author__ = 'Nantes'

from DBNormalizer.view.View import *   # 引入全部视图控件类
from DBNormalizer.model.Model import * # 引入模型层


class Controller():
    # 初始化：创建模型与主窗口/视图，并完成所有事件绑定
    def __init__(self):
        self.model = Model()            # 创建模型对象（负责真正的业务计算）

        # 创建并配置 Tkinter 根窗口
        self.root = Tk()
        self.root.geometry("1000x650+100+50")  # 窗口尺寸与出现位置
        self.root.title("Super DB Normalizer") # 窗口标题
        self.view = View(self.root)     # 创建视图（组合各面板）

        #
        self.current_relation = None    # 当前在左侧树中选中的关系名

        # 事件绑定区：左侧树双击某关系 -> 选中并刷新右侧信息
        self.view.side_panel.relation_tree.tree.bind("<Double-1>", self.select_relation)
        # 连接面板点击“Connect DB” -> 连接数据库并读取元数据
        self.view.connection_panel.connect_button.bind("<Button>", self.get_database_metadata)
        # 右下角“3NF Normalization”按钮 -> 生成 3NF 分解提议
        self.view.right_panel.frame_four_t.subFrame4.\
            buttons_frame.button_normalization.bind("<Button>", self.compute_decomposed_relations3NF)
        # 右下角“BCNF Normalization”按钮 -> 生成 BCNF 分解提议
        self.view.right_panel.frame_four_t.subFrame4.\
            buttons_frame.button_bcnf.bind("<Button>", self.compute_decomposed_relationsBCNF)

        # 左侧树按钮：添加用户关系 / 添加用户属性
        self.view.side_panel.tree_buttons.add_relation_button.bind("<Button>",self.add_user_relation)
        self.view.side_panel.tree_buttons.add_attribute_button.bind("<Button>", self.add_user_attribute)

        # FD 编辑标签页按钮：删除 / 保存 / 新增函数依赖
        self.view.right_panel.frame_two_t.subFrame2.fds_notebook.tab1.fds_buttons_1.\
            button_remove.bind("<Button>", self.remove_fd)
        self.view.right_panel.frame_two_t.subFrame2.fds_notebook.tab1.fds_buttons_1.\
            button_save.bind("<Button>", self.save_relation)
        self.view.right_panel.frame_two_t.subFrame2.fds_notebook.tab1.fds_buttons_1.\
            button_add.bind("<Button>", self.add_fd)

        # “属性闭包”按钮（候选键/属性闭包区域）
        self.view.right_panel.frame_three_t.attributeButton.button_attribute_closure.\
            bind("<Button>", self.get_attr_closure)

        # 连接面板“Export DDL”按钮 -> 把分解结果写成 SQL 建表脚本
        self.view.connection_panel.sql_output_button.bind("<Button>", self.compute_sql_statements)

        self.show_defaults()            # 显示一些默认值（如默认 host）

    # 在 host 输入框填入模型默认主机名
    def show_defaults(self):
        self.view.connection_panel.host.insert(0, self.model.host)

    # 启动图形界面的主循环
    def run(self):
        self.root.mainloop()

    # “Add Relation”回调：弹出对话框，把新关系加入模型并刷新左侧树
    def add_user_relation(self, event):
        inputDialog_rel = MyDialog_Relation(self.root)  # 弹出“输入关系名”对话框
        self.root.wait_window(inputDialog_rel.top)      # 阻塞直到对话框关闭

        print(inputDialog_rel.attr)
        if inputDialog_rel.attr is not None:            # 用户点了“Add”而非取消
            name = inputDialog_rel.attr['attr']
            if not self.model.add_user_relation(name):  # 关系名不重复则加入成功
                # 在左侧树顶层新增该关系节点
                self.view.side_panel.relation_tree.tree.insert('', "end", iid=name, text=name,
                                                             value=['relation', 'original', name])

    # “Add Attribute”回调：为当前选中关系添加一个属性
    def add_user_attribute(self, event):
        inputDialog_rel = MyDialog_Attribute(self.root) # 弹出“输入属性名”对话框
        self.root.wait_window(inputDialog_rel.top)

        if inputDialog_rel.attr is not None:
            name = self.current_relation                # 当前选中的关系
            attr = inputDialog_rel.attr['attr']
            if not self.model.add_user_relation_attribute(name, attr):
                # 属性加入成功后，作为该关系的子节点插入左侧树
                self.view.side_panel.relation_tree.tree.insert(name, "end", text=attr,
                                                             value=['column', 'attr', attr])

    # “Add FD”回调：弹出对话框输入左/右部，构造函数依赖并加入当前关系
    def add_fd(self, event):
        inputDialog = MyDialog(self.root)
        self.root.wait_window(inputDialog.top)

        if inputDialog.fd is not None:                   # 用户确认输入了 FD
            self.model.add_fd(inputDialog.fd, self.current_relation)  # 写入模型
            self.update_right_panel(self.current_relation)            # 刷新右侧面板

    # “Remove FD”回调：删除当前列表中选中的那条 FD
    def remove_fd(self, event):
        fd_idx = self.view.right_panel.frame_two_t.subFrame2.fds_notebook.tab1.fds_table.curselection()
        if len(fd_idx) != 0:                             # 有选中项才删除
            fd = self.view.right_panel.frame_two_t.subFrame2.fds_notebook.tab1.fds_table.selection_get()
            removed = self.model.remove_fd_idx(self.current_relation, fd_idx[0])  # 模型里删除
            self.view.right_panel.frame_two_t.subFrame2.fds_notebook.tab1.fds_table.delete(fd_idx[0])  # 界面删除

    # “Save FD”回调：重新计算当前关系的各规范化指标并刷新界面
    def save_relation(self, event):
        name = self.current_relation
        self.model.update_relation(name)  # 重算 canonical cover / 候选键 / NF
        self.update_right_panel(name)

    # “Attribute Closure”回调：输入属性集合，计算其闭包并列出
    def get_attr_closure(self, event):
        inputDialog2 = MyDialog_AC(self.root)  # 弹出输入框
        print(inputDialog2.attr)
        self.root.wait_window(inputDialog2.top)
 #       print(inputDialog2)
        if inputDialog2.attr is not None:
            # 先清空原来的闭包列表
            self.view.right_panel.frame_three_t.subFrame3_2.attr_closure_list.delete(0,END)
            closure = self.model.get_attr_closure(inputDialog2.attr, self.current_relation)  # 计算闭包
            print(closure)
            for attribute in closure:
                self.view.right_panel.frame_three_t.subFrame3_2.attr_closure_list.insert(END,attribute)

    # 刷新“NF Violations”标签页：显示各范式下的违例 FD
    def update_violations(self):
        self.view.right_panel.frame_two_t.subFrame2.fds_notebook.tab3.text_box.delete(1.0, END)

        # 分别取得 2NF / 3NF / BCNF 违例的 FD 列表
        nf2 = self.model.get_violation(self.current_relation, nf='2NF')
        nf3 = self.model.get_violation(self.current_relation, nf='3NF')
        bcnf = self.model.get_violation(self.current_relation, nf='BCNF')

        # 按小节写入文本框
        self.view.right_panel.frame_two_t.subFrame2.fds_notebook.tab3.text_box.insert(INSERT, '2NF: \n')
        self.view.right_panel.frame_two_t.subFrame2.fds_notebook.tab3.text_box.insert(INSERT, str(nf2))
        self.view.right_panel.frame_two_t.subFrame2.fds_notebook.tab3.text_box.insert(INSERT, "\n3NF: \n")
        self.view.right_panel.frame_two_t.subFrame2.fds_notebook.tab3.text_box.insert(INSERT, str(nf3))
        self.view.right_panel.frame_two_t.subFrame2.fds_notebook.tab3.text_box.insert(INSERT, "\nBCNF: \n")
        self.view.right_panel.frame_two_t.subFrame2.fds_notebook.tab3.text_box.insert(INSERT, str(bcnf))

    # 刷新“Table Information”标签页：显示数据库导入的列、主键、唯一约束信息
    def update_schema_info(self):
        self.view.right_panel.frame_two_t.subFrame2.fds_notebook.tab4.text_box.delete(1.0, END)

        # 取得该关系在数据库中的 schema 信息
        att_schema = self.model.get_relation_db_schema_attributes(self.current_relation)
        unique_schema = self.model.get_relation_db_schema_unique(self.current_relation)
        pk_schema = self.model.get_relation_db_schema_pk(self.current_relation)

        # 显示列（属性）信息
        if att_schema is not None:
            self.view.right_panel.frame_two_t.subFrame2.fds_notebook.tab4.text_box.insert(INSERT, 'ATTRIBUTES: \n')
            for i in att_schema:
                self.view.right_panel.frame_two_t.subFrame2.fds_notebook.tab4.text_box.insert(INSERT, str(i))
                self.view.right_panel.frame_two_t.subFrame2.fds_notebook.tab4.text_box.insert(INSERT, '\n')

        # 显示主键约束
        if pk_schema is not None:
            self.view.right_panel.frame_two_t.subFrame2.fds_notebook.tab4.text_box.insert(INSERT, "\nPK CONSTRAINTS: \n")
            self.view.right_panel.frame_two_t.subFrame2.fds_notebook.tab4.text_box.insert(INSERT, str(pk_schema))
            self.view.right_panel.frame_two_t.subFrame2.fds_notebook.tab4.text_box.insert(INSERT, '\n')

        # 显示唯一约束
        if unique_schema is not None:
            self.view.right_panel.frame_two_t.subFrame2.fds_notebook.tab4.\
                text_box.insert(INSERT, "\nUNIQUE CONSTRAINTS: \n")
            for i in unique_schema:
                self.view.right_panel.frame_two_t.subFrame2.fds_notebook.tab4.text_box.insert(INSERT, str(i))
                self.view.right_panel.frame_two_t.subFrame2.fds_notebook.tab4.text_box.insert(INSERT, '\n')

    # 在左侧树中新增一个关系节点（original=True 表示原始关系，否则为分解出的关系），并把属性加为子节点
    def add_relation_tree(self, parent, relation, original=True):
        if original:
            val = ['relation', 'original', relation.name]
        else:
            val = ['relation', 'decomposition', relation.name]

        par = self.view.side_panel.relation_tree.tree.insert(parent, "end", iid=relation.name, text=relation.name,
                                                             value=val)
        for attr in relation.attributes:  # 把该关系的每个属性挂到节点下面
            self.view.side_panel.relation_tree.tree.insert(par, "end",  text=attr, value=['column', 'attr', attr])

    # 把字典 {关系名: 关系对象} 批量填进左侧树
    def populate_from_relation_dict(self, parent, rel_dic):
        for rel in rel_dic.keys():
            self.add_relation_tree(parent, rel_dic[rel])

    # 删除左侧树中所有“分解(decomposition)”出来的子关系节点（重新分解前先清空旧的）
    def delete_decomposition(self):
        original_names = self.model.get_original_relations_names()
        for name in original_names:
            tree_values = self.view.side_panel.relation_tree.tree.get_children(name)
            for item in tree_values:
                item_values = self.view.side_panel.relation_tree.tree.item(item)
                if item_values['values'][1] == 'decomposition':  # 只删分解节点
                    self.view.side_panel.relation_tree.tree.delete(item)

    # “3NF Normalization”按钮的回调包装
    def compute_decomposed_relations3NF(self, event):
        self.compute_decomposed_relations(decomp='3NF')

    # “BCNF Normalization”按钮的回调包装
    def compute_decomposed_relationsBCNF(self, event):
        self.compute_decomposed_relations(decomp='BCNF')

    # 核心：调用模型计算 3NF/BCNF 分解提议，并把分解出的新关系显示到左侧树
    def compute_decomposed_relations(self, decomp='3NF'):
        self.delete_decomposition()           # 先删除上次的分解节点
        if decomp == '3NF':
            self.model.compute_normalization_proposal(decomp='3NF')   # 计算 3NF 分解
        else:
            self.model.compute_normalization_proposal(decomp='BCNF')  # 计算 BCNF 分解
        #
        print(self.model.relations)
        relation_names = self.model.get_original_relations_names()
        # 对每个原始关系，把其分解出的子关系作为它的子节点加入树
        for name in relation_names:
            decomposition_names = self.model.get_decomposition_names(name)
            for dec_name in decomposition_names:
                rel = self.model.get_relation(dec_name)
                self.add_relation_tree(name, rel, original=False)

    # “Export DDL”按钮回调：让模型生成建表 SQL 脚本（Queries.sql）
    def compute_sql_statements(self,event):
        self.model.compute_sql_statements()

    # 清空右上面板中“关系名 / 范式”两个标签的显示
    def clear_right_panel(self):
        #
        self.view.right_panel.frame_one_t.subFrame1.var_name.set("")
        self.view.right_panel.frame_one_t.subFrame1.var_nf.set("")

    # 选中左侧树的某个“关系”节点时，记录当前关系并刷新右侧全部信息
    def select_relation(self, event):
        item = self.view.side_panel.relation_tree.tree.selection()[0]
        item_values = self.view.side_panel.relation_tree.tree.item(item)
        kind = item_values['values'][0]  # 节点类型：relation / column
        name = item_values['text']
        if kind == 'relation':           # 只有关系节点才刷新（点属性列不处理）
            self.current_relation = name
            self.update_right_panel(name)


    # 右侧面板整体刷新：关系名、范式、候选键、canonical cover、FD、违例、schema 信息
    def update_right_panel(self, name):
            self.clear_right_panel()
            # 关系名与当前范式
            self.view.right_panel.frame_one_t.subFrame1.var_name.set(name)
            nf = self.model.get_NF(name)
            self.view.right_panel.frame_one_t.subFrame1.var_nf.set(nf)

            # 候选键列表
            self.view.right_panel.frame_three_t.subFrame3.keys_list.delete(0,END)
            keys = self.model.get_candidate_keys(name)
            if len(keys) != 0:
                for key in keys:
                    self.view.right_panel.frame_three_t.subFrame3.keys_list.insert(END, list(key))

            # 最小覆盖(Canonical cover)列表
            self.view.right_panel.frame_two_t.subFrame2.fds_notebook.tab2.cover_table.delete(0, END)
            cc = self.model.get_canonical_cover(name)
            if cc is not None:
                for fd in cc:
                    self.view.right_panel.frame_two_t.subFrame2.fds_notebook.tab2.cover_table.insert(END, fd)

            # 函数依赖(FD)列表
            self.view.right_panel.frame_two_t.subFrame2.fds_notebook.tab1.fds_table.delete(0,END)
            fds = self.model.get_fds(name)
            if len(fds) != 0:
                for fd in fds:
                    self.view.right_panel.frame_two_t.subFrame2.fds_notebook.tab1.fds_table.insert(END,fd)

            # 各范式违例信息
            self.update_violations()

            # 数据库 schema 信息
            self.update_schema_info()

    # “Connect DB”回调：从输入框读取连接参数，连接数据库并导入所有表(含自动发现 FD)
    def get_database_metadata(self, event):
        # 从连接面板读取连接参数
        host = self.view.connection_panel.host.get()
        port = self.view.connection_panel.port.get()
        username = self.view.connection_panel.username.get()
        password = self.view.connection_panel.password.get()
        database = self.view.connection_panel.database.get()

        self.model = Model()              # 重新创建一个全新模型（清空旧状态）

        # 保存连接参数
        self.model.set_db_connection_params(username, password, host, database, port)

        # 依次：连接数据库读取元数据 -> 转为关系对象 -> 依据数据发现 FD
        self.model.get_metadata()
        self.model.get_schema()
        self.model.append_fds()

        # 刷新左侧树：先清空整棵树，再加一个空根节点，然后把全部关系填进去
        self.view.side_panel.relation_tree.delete_tree()
        self.view.side_panel.relation_tree.tree.insert('', "end", text='')
        self.populate_from_relation_dict('', self.model.relations)
        #
