# -*- coding: utf-8 -*-
"""准确范式分析器：数据库 -> FD(数据挖掘 + schema PK/UK) -> NF(正确判定) -> JSON 报告。

FD 来源（互补）：
  * from_data   —— 从数据分区挖掘，是判定的事实来源，能发现 DDL 没声明的语义依赖；
  * from_schema —— 由 PRIMARY KEY / UNIQUE 推导，作为零成本兜底（DDL 漏写键时补上）。

判定依据由 fd_policy 决定：
  * "union"（默认）—— 数据 FD ∪ schema FD，最保守；
  * "data"          —— 只信数据挖掘，schema 键仅在上报中提示、不参与判定。

数据左侧区分度过低(可能是小数据巧合)的 FD 会在 low_confidence_data_fds 中提示。

对外主接口：
    NFAnalyzer(engine).analyze_all_tables(target_nf, fd_policy="union") -> dict
"""
from sqlalchemy import inspect

from . import nf_core
from .miner import mine_fds
from .decomposer import propose
from .fds import FD, fd_to_str, sort_key

NF_RANK = {"1NF": 1, "2NF": 2, "3NF": 3, "BCNF": 4}

# 低于该分区块数的数据 FD 会被标注为"低区分度/可能巧合"
WARN_LHS_GROUPS = 3


class NFAnalyzer:
    """包装数据库与判定核心，产出给 LLM 的准确报告。"""

    def __init__(self, engine):
        self.engine = engine

    def analyze_all_tables(self, target_nf, with_decomposition=True, fd_policy="union"):
        insp = inspect(self.engine)
        reports = {}
        for table in insp.get_table_names():
            attributes = [col["name"] for col in insp.get_columns(table)]
            data_fds, _, support = mine_fds(self.engine, table, attributes)
            schema_fds, declared_keys = schema_fds_from_inspector(insp, table, attributes)
            reports[table] = analyze_relation(
                attributes,
                data_fds,
                target_nf,
                with_decomposition,
                schema_fds=schema_fds,
                declared_keys=declared_keys,
                support=support,
                fd_policy=fd_policy,
            )
        return {
            "passed": all(r["passed"] for r in reports.values()),
            "target_nf": target_nf,
            "fd_policy": fd_policy,
            "tables": reports,
        }


def _key_to_fds(columns, attrs):
    """把一列键 (PK 或 UNIQUE 的列组合) 转成 columns -> 其余每个属性的 FD。"""
    lhs = frozenset(columns)
    others = set(attrs) - lhs
    if not others:
        return set()
    return {FD(lhs, frozenset([attr])) for attr in others}


def schema_fds_from_inspector(insp, table, attributes):
    """从数据库 schema 的 PRIMARY KEY / UNIQUE 推导保证成立的 FD。

    :return: (fds, declared_keys)
    """
    attrs = set(attributes)
    fds = set()
    declared_keys = []

    pk = insp.get_pk_constraint(table) or {}
    pk_cols = pk.get("constrained_columns") or []
    if pk_cols:
        declared_keys.append(list(pk_cols))
        fds |= _key_to_fds(pk_cols, attrs)

    seen = {frozenset(pk_cols)} if pk_cols else set()
    for uc in insp.get_unique_constraints(table) or []:
        cols = uc.get("column_names") or []
        if not cols:
            continue
        key = frozenset(cols)
        if key in seen:
            continue
        seen.add(key)
        declared_keys.append(list(cols))
        fds |= _key_to_fds(cols, attrs)

    return fds, declared_keys


def _decomp_target(target_nf):
    return "BCNF" if target_nf == "BCNF" else "3NF"


def analyze_relation(
    attributes,
    fds,
    target_nf="BCNF",
    with_decomposition=True,
    schema_fds=None,
    declared_keys=None,
    support=None,
    fd_policy="union",
):
    """对单个关系判定范式并生成报告（不需要数据库，便于测试）。

    :param fds: 数据挖掘得到的 FD 集合
    :param schema_fds: 由 PK/UK 推导的 FD 集合（可选）
    :param declared_keys: schema 中声明的键列表（可选）
    :param support: {FD: 左部分区块数}（可选）
    :param fd_policy: "union"（数据 ∪ schema，默认）或 "data"（只用数据）
    """
    schema_fds = set(schema_fds or set())
    declared_keys = list(declared_keys or [])
    support = dict(support or {})
    if fd_policy == "data":
        all_fds = set(fds)
    else:
        all_fds = set(fds) | schema_fds

    result = nf_core.analyze(attributes, all_fds)
    nf = result["nf"]

    warnings = []
    if nf == "NoFDs":
        warnings.append(
            "未检测到函数依赖：可能是测试数据过少（如仅 1 行）或属性取值过于单一，"
            "无法据此判断范式，请补充更有代表性的数据"
        )

    if nf == "NoFDs":
        passed = True
    else:
        passed = NF_RANK.get(nf, 0) >= NF_RANK.get(target_nf, 4)

    low_confidence = []
    for fd in sorted(fds, key=sort_key):
        groups = support.get(fd)
        if groups is not None and groups < WARN_LHS_GROUPS:
            low_confidence.append(
                {
                    "fd": fd_to_str(fd),
                    "lhs_groups": groups,
                    "reason": f"左部只区分出 {groups} 组取值，可能是小数据导致的巧合依赖",
                }
            )

    report = {
        "attributes": sorted(attributes),
        "current_nf": nf,
        "target_nf": target_nf,
        "passed": passed,
        "fd_policy": fd_policy,
        "candidate_keys": [sorted(k) for k in result["candidate_keys"]],
        "minimal_cover": [fd_to_str(fd) for fd in sorted(result["minimal_cover"], key=sort_key)],
        "fds": [fd_to_str(fd) for fd in sorted(all_fds, key=sort_key)],
        "fd_sources": {
            "from_data": [fd_to_str(fd) for fd in sorted(fds, key=sort_key)],
            "from_schema": [fd_to_str(fd) for fd in sorted(schema_fds, key=sort_key)],
        },
        "declared_keys": declared_keys,
        "low_confidence_data_fds": low_confidence,
        "violations": result["violations"],
        "warnings": warnings,
    }

    if not passed and with_decomposition:
        try:
            report["decomposition"] = propose(
                set(attributes),
                result["minimal_cover"],
                all_fds,
                target=_decomp_target(target_nf),
            )
        except Exception as exc:  # 分解失败不应阻断报告
            report["decomposition_error"] = f"{type(exc).__name__}: {exc}"
    return report
