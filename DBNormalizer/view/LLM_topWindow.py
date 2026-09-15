# -*- coding: utf-8 -*-
# LLM_topWindow：LLM 迭代设计 DDL 的对话窗口。
# 顶部输入需求与目标范式，点击“开始”后，下方实时显示每轮提交的 DDL、
# 范式分析报告与最终结果；窗口保持合适的初始尺寸且可缩放。
__author__ = 'Nantes'

from tkinter import *
from tkinter import ttk


class LLMWindow:
    # 构造对话窗口并布局
    def __init__(self, parent):
        top = self.top = Toplevel(parent)               # 子窗口
        self.top.title("LLM Normalize")
        self.top.geometry("820x620+140+60")             # 合适的初始尺寸
        self.top.minsize(560, 420)                      # 允许缩放，但有下限
        self.parent = parent
        self.on_start = None                            # 由 Controller 注入的开始回调

        # ---- 输入区：需求 + 目标范式 ----
        input_frame = LabelFrame(top, text="需求")
        input_frame.pack(side=TOP, fill=X, padx=8, pady=(8, 4))

        self.entry = Text(input_frame, height=4, wrap="word")
        self.entry.pack(side=TOP, fill=X, padx=6, pady=6)

        bar = Frame(input_frame)
        bar.pack(side=TOP, fill=X, padx=6, pady=(0, 6))

        Label(bar, text="目标范式：").pack(side=LEFT)
        self.nf = StringVar(value="BCNF")
        self.nf_box = ttk.Combobox(bar, textvariable=self.nf, state="readonly",
                                   values=["2NF", "3NF", "BCNF"], width=8)
        self.nf_box.pack(side=LEFT)
        self.start_button = Button(bar, text="开始", command=self._start)
        self.start_button.pack(side=RIGHT)

        # ---- 底部状态栏 ----
        self.status = Label(top, text="请输入需求后点击“开始”", anchor="w")
        self.status.pack(side=BOTTOM, fill=X, padx=8, pady=(4, 8))

        # ---- 中部：可滚动的对话文本区 ----
        body = Frame(top)
        body.pack(side=TOP, expand=1, fill=BOTH, padx=8, pady=(4, 0))

        self.text = Text(body, wrap="word", state="disabled")
        scroll = Scrollbar(body, command=self.text.yview)
        self.text.configure(yscrollcommand=scroll.set)
        scroll.pack(side=RIGHT, fill=Y)
        self.text.pack(side=LEFT, expand=1, fill=BOTH)

        self.top.transient(parent)                      # 随主窗口

    # “开始”回调：读取需求与目标范式，交给 Controller 启动后台任务
    def _start(self):
        request = self.entry.get("1.0", "end").strip()
        if not request:
            self.set_status("请先输入需求")
            return
        self.start_button.configure(state="disabled")
        self.entry.configure(state="disabled")
        self.nf_box.configure(state="disabled")
        if self.on_start is not None:
            self.on_start(request, self.nf.get())

    # 追加一段对话内容（供主线程调用）
    def append(self, text):
        self.text.configure(state="normal")
        self.text.insert("end", str(text) + "\n\n")
        self.text.see("end")
        self.text.configure(state="disabled")

    # 更新底部状态
    def set_status(self, text):
        self.status.configure(text=str(text))
