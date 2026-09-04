# -*- coding: utf-8 -*-
# AC_topWindow：用于“计算属性闭包”的顶层对话框。
# 用户输入若干属性后点 Add，结果存到 self.attr（形如 {'attr':'A,B'}），
# 由 Controller 计算这些属性的闭包并显示。
__author__ = 'Nantes'


from tkinter import *

class MyDialog_AC:
    # 构造弹窗并布局
    def __init__(self, parent):
        top = self.top = Toplevel(parent)   # 子窗口
        self.top.geometry("300x120+150+100")
        self.top.resizable(0,0)             # 禁止缩放
        self.parent = parent
        self.myLabel = Label(top, text='Add attributes')
        self.myLabel.pack()

        # 属性输入框
        self.myEntryBox = Entry(top)
        self.myEntryBox.pack(side=TOP, expand=1, fill=X)

        # Add / Cancel 按钮
        self.mySubmitButton_ac = Button(top, text='Add', command=self.send)
        self.mySubmitButton_ac.pack(side=LEFT, expand= 1)
        self.cancel_button = Button(top, text='Cancel', command=self.cancel)
        self.cancel_button.pack(side=LEFT, expand=1)

        self.attr = None                    # 保存输入（None=取消）
        self.top.transient(self.parent)
        self.top.grab_set()                 # 模态窗口
        #self.parent.wait_window(top)

    # “Add”回调：保存输入属性并关闭
    def send(self):
        self.attr = {'attr':self.myEntryBox.get()}
        self.top.destroy()

    # “Cancel”回调：关闭（attr 保持 None）
    def cancel(self):
        self.top.destroy()
