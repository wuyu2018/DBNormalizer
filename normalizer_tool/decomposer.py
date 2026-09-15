# -*- coding: utf-8 -*-
"""分解提议：复用现有 DBNormalizer.model.Decomp，并对结果做正确性复验。

分解算法(3NF 合成 / BCNF 递归拆分 / FD 投影)本身质量良好，直接复用；
但 Decomp 内部仍依赖旧版判定代码，故对每个子关系再用 nf_core 重新判定，
在输出中标注其实际范式，供上层(LLM)判断分解是否达标。
"""
from contextlib import redirect_stdout
from io import StringIO

from DBNormalizer.model.Decomp import Decomposition

from . import nf_core
from .fds import to_legacy, from_legacy, fd_to_str, sort_key


def propose(all_attrs, minimal_cover, fds, target="3NF"):
    """生成分解提议。

    :param all_attrs: 原关系属性集合
    :param minimal_cover: nf_core 求得的最小覆盖（FD 集合）
    :param fds: 原始挖掘到的 FD 集合
    :param target: '3NF' 或 'BCNF'
    :return: 子关系列表，每项含 attributes / fds / candidate_keys / nf / reached
    """
    dec = Decomposition()
    r = set(all_attrs)
    cover_legacy = to_legacy(minimal_cover)
    fds_legacy = to_legacy(fds)

    if target == "BCNF":
        with redirect_stdout(StringIO()):
            proposal = dec.proposalBCNF(r, cover_legacy)
    else:
        with redirect_stdout(StringIO()):
            proposal = dec.proposal3NF(r, cover_legacy, fds_legacy)

    result = []
    for attrs_set, sub_fd_list in proposal:
        attrs = set(attrs_set)
        sub_fds = from_legacy(sub_fd_list)
        sub = nf_core.analyze(attrs, sub_fds)
        result.append(
            {
                "attributes": sorted(attrs),
                "minimal_cover": [fd_to_str(fd) for fd in sorted(sub["minimal_cover"], key=sort_key)],
                "candidate_keys": [sorted(k) for k in sub["candidate_keys"]],
                "nf": sub["nf"],
            }
        )
    return result
