# -*- coding: utf-8 -*-
"""LLM 驱动的 "写 DDL -> 写库 -> 分析范式 -> 改 DDL" 循环（方案 B，供 GUI 调用）。

宿主驱动交替：
  * LLM 只负责生成 DDL/数据，且只暴露一个工具 submit_ddl；
  * 每轮：宿主强制 LLM 调 submit_ddl 写库 -> 宿主直接调 NFAnalyzer 分析
         -> 报告回传给 LLM -> 未通过则进入下一轮，通过则让 LLM 输出最终 DDL；
  * engine 由调用方注入（GUI 的 Model 由连接表单建好后传入），LLM 永远拿不到连接串。

依赖：pip install openai（本模块延迟导入，未装也不影响 GUI 启动）。
"""
import json
import os

from sqlalchemy import inspect, text
from normalizer_tool.tools import tools
from normalizer_tool.analyzer import NFAnalyzer


def analyze_all_tables(engine, target_nf="BCNF"):
    return NFAnalyzer(engine).analyze_all_tables(target_nf)


def build_dispatch(engine):
    """把 engine 注入工具实现。返回 {工具名: 可调用对象}，签名与 tools.py 一致。"""

    def submit_ddl(ddl: str, data: str) -> str:
        with engine.connect() as conn:
            for stmt in (ddl + ";" + data).split(";"):
                stmt = stmt.strip()
                if stmt:
                    conn.execute(text(stmt))
            conn.commit()
        return "success"

    def analyze_tables():
        return analyze_all_tables(engine)

    return {
        "submit_ddl": submit_ddl,
        "analyze_all_tables": analyze_tables,
    }

SYSTEM_PROMPT = """你是一个数据库业务设计助手。工作流程：
1. 根据用户需求设计完整的 DDL(CREATE TABLE) 和测试数据(INSERT INTO，初次写入时你应该严格根据现实中的实际业务语境写入不少于20条符合你的ddl关系结构的data)，调用 submit_ddl 写入数据库；
2. 写库后，按照设计你会自动调用工具对该库做范式分析，并让其把结构化报告发给你；
3. 若报告 passed 为 false，参考其中的 violations / decomposition 等一切可能的判断修改你的设计，再次调用 submit_ddl 覆盖写入上一次你写的ddl（当然初次写入不计）；
4. 若 passed 为 true，停止调用工具。

注意：每次都要提交"完整"的 DDL，重要的是每次提交你都要根据实际业务和关系结构插入至少10条数据。"""


def _client():
    """延迟创建 OpenAI 客户端，避免未安装 openai 时影响 GUI 导入。"""
    from openai import OpenAI

    return OpenAI(
        api_key=os.environ.get("DEEPSEEK_API_KEY", ""),
        base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
    )

messages = [
    {
        "role": "user",
        "content": "在用户给出具体需求后，根据用户需求结合业务语义设计数据库，最终是需要可执行的ddl语句",
    }
]


class MessageWindow:
    """LLM 对话窗口：只保留必要上下文，避免历史随轮数无限增长。

    固定部分：SYSTEM_PROMPT + 调用方传入的初始消息（含原始需求）；
    每轮刷新：上一轮提交的 DDL/数据 + 本次范式报告。
    """

    def __init__(self, base):
        self.base = list(base)
        self.last_ddl = None
        self.last_data = None
        self.report = None

    def record_submission(self, ddl, data):
        self.last_ddl = ddl or ""
        self.last_data = data or ""

    def record_report(self, report):
        self.report = report

    def build(self):
        window = [{"role": "system", "content": SYSTEM_PROMPT}] + list(self.base)
        if self.last_ddl is not None:
            window.append({
                "role": "assistant",
                "content": "上一轮提交的 DDL：\n" + self.last_ddl + "\n测试数据：\n" + self.last_data,
            })
        if self.report is not None:
            window.append({
                "role": "user",
                "content": "范式分析报告（JSON）：\n" + json.dumps(self.report, ensure_ascii=False),
            })
        return window


def run_turn(engine, messages, target_nf="BCNF", on_event=None):
    """驱动 LLM 迭代设计 DDL，并通过 on_event 回调实时上报进度。

    :param target_nf: 目标范式 (2NF/3NF/BCNF)
    :param on_event: 可选回调，接收进度字符串（供 GUI 对话窗口显示）
    """

    def emit(msg):
        if on_event is not None:
            on_event(msg)

    def analyze_current():
        """分析当前库，返回 (报告, 是否通过)。

        空库一律视为“未通过”，避免 analyze_all_tables 对空库返回真空 passed=True，
        导致循环条件把“还没建出任何表”误判成“已满足目标范式”。
        """
        report = analyze_all_tables(engine, target_nf)
        has_tables = bool(inspect(engine).get_table_names())
        return report, (has_tables and report["passed"])

    dispatch = build_dispatch(engine)
    window = MessageWindow(messages)

    # 已有库：先分析现状，把报告交给 LLM 作为起点；空库则直接进入设计循环
    report, passed = analyze_current()
    if report["tables"]:
        window.record_report(report)
        emit("检测到已有数据库，初始范式报告：passed=%s" % passed)

    rnd = 0
    response = None
    while not passed:
        rnd += 1
        response = _client().chat.completions.create(
            model='deepseek-flash',
            messages=window.build(),
            tools=tools,
            reasoning_effort="high",
            tool_choice= "required",
            extra_body={ "thinking": { "type": "disabled" } },
        )
        message = response.choices[0].message
        tool_calls = message.tool_calls
        if tool_calls is None:
            break
        for tool in tool_calls:
            args = json.loads(tool.function.arguments)
            tool_function = dispatch[tool.function.name]
            tool_result = tool_function(**args)
            if tool.function.name == "submit_ddl":
                window.record_submission(args.get("ddl"), args.get("data"))
                emit("第 %d 轮 · 提交 DDL\n%s" % (rnd, args.get("ddl", "")))
            print(f"tool result for {tool.function.name}: {tool_result}\n")
        report, passed = analyze_current()
        window.record_report(report)
        emit("第 %d 轮 · 分析结果 passed=%s\n%s"
             % (rnd, passed, json.dumps(report, ensure_ascii=False)))

    # 通过后让 LLM 输出最终 DDL（只要结构，不要测试数据）
    final = _client().chat.completions.create(
        model='deepseek-flash',
        messages=window.build() + [
            {"role": "user", "content": "请给出最终完整、可执行的 DDL 及简要说明。"
                                        "只输出建表等结构语句，不要输出 INSERT 测试数据。"}
        ],
        extra_body={ "thinking": { "type": "disabled" } },
    )
    return final.choices[0].message.content





