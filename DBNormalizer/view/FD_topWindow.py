# -*- coding: utf-8 -*-
# FD_topWindow：用于“添加函数依赖”的顶层对话框。
# 提供两个输入框（左部 LHS / 右部 RHS）与 Add / Cancel 按钮，
# 用户点 Add 后把结果存到 self.fd（形如 {'lhs':'...','rhs':'...'}），
# Controller 再据此构造 FDependency 并加入关系。
__author__ = 'Nantes'

from tkinter import *

class MyDialog:
    # 构造弹窗并布局
    def __init__(self, parent):
        top = self.top = Toplevel(parent)   # 子窗口
        self.top.geometry("400x150+100+50")
        self.top.resizable(0,0)             # 禁止缩放
        self.parent = parent
        self.myLabel = Label(top, text='Add functional dependency')
        self.myLabel.pack()

        # 左部输入框
        self.myEntryBox_left = Entry(top)
        self.myEntryBox_left.pack(expand=1, fill=X)

        # 右部输入框
        self.myEntryBox_right = Entry(top)
        self.myEntryBox_right.pack(expand=1, fill=X)

        # Add / Cancel 按钮
        self.mySubmitButton = Button(top, text='Add', command=self.send)
        self.mySubmitButton.pack()
        self.cancel_button = Button(top, text='Cancel', command=self.cancel)
        self.cancel_button.pack()

        self.fd = None                      # 保存用户输入的 FD（None=取消）
        self.top.transient(self.parent)     # 设为父窗口的子窗口
        self.top.grab_set()                 # 模态：独占输入焦点
        #self.parent.wait_window(top)

    # “Add”回调：组装 fd 字典并关闭窗口
    def send(self):
        self.fd = {'lhs':self.myEntryBox_left.get(), 'rhs':self.myEntryBox_right.get()}
        self.top.destroy()

    # “Cancel”回调：直接关闭（self.fd 保持 None）
    def cancel(self):
        self.top.destroy()
