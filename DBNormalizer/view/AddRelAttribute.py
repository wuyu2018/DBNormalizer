# -*- coding: utf-8 -*-
# AddRelAttribute：两个弹窗对话框。
#   MyDialog_Relation  ：输入“新关系名”
#   MyDialog_Attribute ：输入“新属性名”
# 用户输入后点 Add，结果分别存到 self.attr，由 Controller 调模型新增关系/属性。
__author__ = 'Nantes'

from tkinter import *

class MyDialog_Relation:
    # 输入关系名的对话框
    def __init__(self, parent):
        top = self.top = Toplevel(parent)
        self.parent = parent
        self.top.geometry("300x120+150+100")
        self.top.resizable(0,0)
        self.myLabel = Label(top, text='Add Relation Name')
        self.myLabel.pack()

        self.myEntryBox = Entry(top)         # 关系名输入框
        self.myEntryBox.pack(side=TOP, expand=1, fill=X)

        self.mySubmitButton_ac = Button(top, text='Add', command=self.send)
        self.mySubmitButton_ac.pack(side=LEFT, expand= 1)
        self.cancel_button = Button(top, text='Cancel', command=self.cancel)
        self.cancel_button.pack(side=LEFT, expand=1)

        self.attr = None                     # 保存结果（None=取消）
        self.top.transient(self.parent)
        self.top.grab_set()
        #self.parent.wait_window(top)

    # “Add”：保存关系名并关闭
    def send(self):
        self.attr = {'attr':self.myEntryBox.get()}
        self.top.destroy()

    # “Cancel”：关闭（attr 保持 None）
    def cancel(self):
        self.top.destroy()


class MyDialog_Attribute:
    # 输入属性名的对话框
    def __init__(self, parent):
        top = self.top = Toplevel(parent)
        self.top.geometry("300x120+150+100")
        self.top.resizable(0,0)
        self.parent = parent
        self.myLabel = Label(top, text='Add Attribute Name')
        self.myLabel.pack()

        self.myEntryBox = Entry(top)         # 属性名输入框
        self.myEntryBox.pack(side=TOP, expand=1, fill=X)

        self.mySubmitButton_ac = Button(top, text='Add', command=self.send)
        self.mySubmitButton_ac.pack(side=LEFT, expand= 1)
        self.cancel_button = Button(top, text='Cancel', command=self.cancel)
        self.cancel_button.pack(side=LEFT, expand=1)

        self.attr = None
        self.top.transient(self.parent)
        self.top.grab_set()
        #self.parent.wait_window(top)

    # “Add”：保存属性名并关闭
    def send(self):
        self.attr = {'attr':self.myEntryBox.get()}
        self.top.destroy()

    # “Cancel”：关闭（attr 保持 None）
    def cancel(self):
        self.top.destroy()
