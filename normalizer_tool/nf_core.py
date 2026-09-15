# -*- coding: utf-8 -*-
"""正确、确定的规范化判定核心。

与现有 DBNormalizer.model.Normalization 的区别（也是准确性的关键）：
  * 3NF/BCNF 用"超键"(closure(lhs) == 全体属性)判断，而不是"lhs 恰好等于某个候选键"；
  * 最小覆盖逐属性消去并迭代到不动点，且所有遍历顺序固定，结果确定；
  * 候选键严格基于闭包枚举 + 超集剪枝；
  * 2NF 通过"去掉候选键中任一属性后的闭包是否含非主属性"来判定，可捕获隐含的部分依赖。

本模块不依赖数据库与界面，可独立单元测试。
"""
from itertools import combinations

from .fds import FD, fd_to_str, sort_key


def closure(fds, attrs):
    """属性闭包：反复并入左部已被包含的 FD 的右部，直到收敛。"""
    result = set(attrs)
    changed = True
    while changed:
        changed = False
        for fd in fds:
            if fd.lhs <= result and not fd.rhs <= result:
                result |= fd.rhs
                changed = True
    return frozenset(result)


def is_superkey(fds, all_attrs, lhs):
    """lhs 是否为超键：其闭包覆盖全部属性。"""
    return closure(fds, lhs) == frozenset(all_attrs)


def _right_singleton(fds):
    work = set()
    for fd in fds:
        for attr in fd.rhs:
            work.add(FD(fd.lhs, frozenset([attr])))
    return work


def minimal_cover(fds):
    """最小(规范)覆盖：右部单值化 -> 消去左部多余属性 -> 删除冗余依赖。

    与旧实现不同，这里对每个左部属性逐一尝试消去，并迭代到不动点，
    遍历顺序固定，因此结果确定且真正最小。
    """
    work = _right_singleton(fds)

    # 消去左部多余属性：若去掉 b 后仍能推出 rhs，则 b 多余
    changed = True
    while changed:
        changed = False
        for fd in sorted(work, key=sort_key):
            if fd not in work or len(fd.lhs) <= 1:
                continue
            for attr in sorted(fd.lhs):
                reduced = fd.lhs - {attr}
                if fd.rhs <= closure(work, reduced):
                    work.discard(fd)
                    work.add(FD(frozenset(reduced), fd.rhs))
                    changed = True
                    break

    # 删除冗余依赖：若去掉该 FD 后 rhs 仍可从 lhs 推出，则冗余
    for fd in sorted(work, key=sort_key):
        if fd not in work:
            continue
        if fd.rhs <= closure(work - {fd}, fd.lhs):
            work.discard(fd)
    return work


def candidate_keys(all_attrs, fds):
    """求出全部候选键（frozenset 列表，结果确定）。

    一定属于每个键的属性 = 从未出现在任何右部的属性；
    其余属性按大小递增枚举，闭包覆盖全集者为键，并剪掉已找到键的超集。
    """
    all_attrs = frozenset(all_attrs)
    rhs_attrs = set()
    for fd in fds:
        rhs_attrs |= fd.rhs
    must = set(all_attrs) - rhs_attrs

    if closure(fds, must) == all_attrs:
        return [frozenset(must)]

    rest = sorted(all_attrs - must)
    keys = []
    for size in range(1, len(rest) + 1):
        for combo in combinations(rest, size):
            cand = frozenset(must | set(combo))
            if any(k <= cand for k in keys):
                continue
            if closure(fds, cand) == all_attrs:
                keys.append(cand)
    return keys


def prime_attributes(keys):
    """主属性集合：出现在任一候选键中的属性。"""
    primes = set()
    for key in keys:
        primes |= set(key)
    return primes


def _violation_2nf(subset, attr, key):
    subset_s = ', '.join(sorted(subset))
    key_s = ', '.join(sorted(key))
    return {
        "fd": f"{subset_s} -> {attr}",
        "level": "2NF",
        "reason": (
            f"非主属性 {attr} 部分依赖于候选键 {{{key_s}}} 的真子集 "
            f"{{{subset_s}}}（部分依赖）"
        ),
        "fix_suggestion": (
            f"消除部分依赖：把 {attr} 及由 {{{subset_s}}} 决定的其它非主属性"
            f"拆到以 {{{subset_s}}} 为主键的独立新表"
        ),
    }


def _violation_3nf(fd, attr):
    lhs_s = ', '.join(sorted(fd.lhs))
    return {
        "fd": f"{lhs_s} -> {attr}",
        "level": "3NF",
        "reason": f"左部 {{{lhs_s}}} 不是超键，右部 {attr} 是非主属性（传递依赖）",
        "fix_suggestion": (
            f"消除传递依赖：拆出以 {{{lhs_s}}} 为主键的新表，存放 {attr} 等由它决定的属性"
        ),
    }


def _violation_bcnf(fd):
    lhs_s = ', '.join(sorted(fd.lhs))
    return {
        "fd": fd_to_str(fd),
        "level": "BCNF",
        "reason": f"左部 {{{lhs_s}}} 不是超键",
        "fix_suggestion": (
            f"沿 {fd_to_str(fd)} 做 BCNF 分解：新表以 {{{lhs_s}}} 为键并包含其闭包属性，"
            f"其余属性留在原表"
        ),
    }


def check_2nf(all_attrs, fds, keys):
    """2NF 违例：候选键的某个真子集决定了某个非主属性。"""
    all_attrs = frozenset(all_attrs)
    primes = prime_attributes(keys)
    non_primes = sorted(all_attrs - primes)
    out = []
    for key in sorted(keys, key=lambda k: (len(k), sorted(k))):
        if len(key) <= 1:
            continue
        for attr in sorted(key):
            subset = key - {attr}
            covered = closure(fds, subset)
            for non_prime in non_primes:
                if non_prime in covered:
                    out.append(_violation_2nf(subset, non_prime, key))
                    break
    return out


def check_3nf(all_attrs, fds, keys):
    """3NF 违例：左部不是超键且右部含非主属性。"""
    all_attrs = frozenset(all_attrs)
    primes = prime_attributes(keys)
    out = []
    for fd in sorted(fds, key=sort_key):
        if is_superkey(fds, all_attrs, fd.lhs):
            continue
        for attr in sorted(fd.rhs):
            if attr not in primes:
                out.append(_violation_3nf(fd, attr))
    return out


def check_bcnf(all_attrs, fds, keys):
    """BCNF 违例：存在左部不是超键的非平凡 FD。"""
    all_attrs = frozenset(all_attrs)
    out = []
    for fd in sorted(fds, key=sort_key):
        if fd.rhs <= fd.lhs:
            continue
        if not is_superkey(fds, all_attrs, fd.lhs):
            out.append(_violation_bcnf(fd))
    return out


def _dedupe(violations):
    seen = set()
    result = []
    for v in violations:
        sig = (v["fd"], v["level"])
        if sig in seen:
            continue
        seen.add(sig)
        result.append(v)
    return result


def analyze(all_attrs, fds):
    """完整判定：返回范式等级、最小覆盖、候选键与违例明细。

    :param all_attrs: 属性名集合
    :param fds: FD 集合（frozenset 表示）
    :return: dict(nf, minimal_cover, candidate_keys, violations)
    """
    all_attrs = frozenset(all_attrs)
    if not fds:
        return {
            "nf": "NoFDs",
            "minimal_cover": set(),
            "candidate_keys": [],
            "violations": [],
        }

    cover = minimal_cover(fds)
    keys = candidate_keys(all_attrs, cover)

    v2 = check_2nf(all_attrs, cover, keys)
    v3 = check_3nf(all_attrs, cover, keys)
    vb = check_bcnf(all_attrs, cover, keys)

    if v2:
        nf = "1NF"
    elif v3:
        nf = "2NF"
    elif vb:
        nf = "3NF"
    else:
        nf = "BCNF"

    return {
        "nf": nf,
        "minimal_cover": cover,
        "candidate_keys": keys,
        "violations": _dedupe(v2 + v3 + vb),
    }
