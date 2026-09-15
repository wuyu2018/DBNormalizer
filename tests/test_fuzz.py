# -*- coding: utf-8 -*-
"""用独立实现的暴力参考算法，对 nf_core 做随机对拍，验证判定正确性。

参考实现完全不共用 nf_core 的代码路径：
  * 候选键：枚举全部子集，闭包=全集且无更小子集为键；
  * 2NF/3NF/BCNF：按定义枚举全部子集 X 与 X+ 判定。

运行：
    python -m unittest tests.test_fuzz -v
"""
import random
import unittest
from itertools import combinations

from normalizer_tool import nf_core
from normalizer_tool.fds import FD


# ---------- 独立参考实现 ----------
def closure_ref(fds, x):
    result = set(x)
    changed = True
    while changed:
        changed = False
        for fd in fds:
            if fd.lhs <= result and not fd.rhs <= result:
                result |= fd.rhs
                changed = True
    return frozenset(result)


def all_subsets(attrs, min_size=0):
    attrs = sorted(attrs)
    for size in range(min_size, len(attrs) + 1):
        for combo in combinations(attrs, size):
            yield frozenset(combo)


def keys_ref(attrs, fds):
    attrs = frozenset(attrs)
    found = []
    for size in range(1, len(attrs) + 1):
        for cand in all_subsets(attrs, size):
            if len(cand) != size:
                continue
            if closure_ref(fds, cand) == attrs:
                if not any(k < cand for k in found):
                    found.append(cand)
    return found


def nf_ref(attrs, fds):
    attrs = frozenset(attrs)
    if not fds:
        return "NoFDs"
    keys = keys_ref(attrs, fds)
    primes = set()
    for k in keys:
        primes |= set(k)

    violate_2nf = False
    for key in keys:
        for subset in all_subsets(key, 1):
            if subset == key:
                continue
            covered = closure_ref(fds, subset)
            if any(a not in primes for a in covered - subset):
                violate_2nf = True

    violate_3nf = False
    for x in all_subsets(attrs, 1):
        plus = closure_ref(fds, x)
        if plus == attrs:
            continue
        if any(a not in primes for a in plus - x):
            violate_3nf = True

    violate_bcnf = False
    for x in all_subsets(attrs, 1):
        plus = closure_ref(fds, x)
        if plus != attrs and plus != x:
            violate_bcnf = True

    if violate_2nf:
        return "1NF"
    if violate_3nf:
        return "2NF"
    if violate_bcnf:
        return "3NF"
    return "BCNF"


def random_fds(attrs, rng, max_fds=4):
    attrs = list(attrs)
    fds = set()
    for _ in range(rng.randint(1, max_fds)):
        lhs = frozenset(rng.sample(attrs, rng.randint(1, max(1, len(attrs) - 1))))
        remaining = [a for a in attrs if a not in lhs]
        if not remaining:
            continue
        rhs = frozenset(rng.sample(remaining, rng.randint(1, len(remaining))))
        fds.add(FD(lhs, rhs))
    return fds


class TestFuzzAgainstReference(unittest.TestCase):
    def test_nf_matches_reference(self):
        rng = random.Random(20240914)
        checked = 0
        for _ in range(2000):
            n = rng.randint(2, 5)
            attrs = frozenset("abcde"[:n])
            fds = random_fds(attrs, rng)
            if not fds:
                continue
            checked += 1

            got = nf_core.analyze(attrs, fds)["nf"]
            expected = nf_ref(attrs, fds)
            self.assertEqual(
                got, expected,
                msg=f"NF mismatch attrs={sorted(attrs)} fds={sorted(str(f) for f in fds)} got={got} exp={expected}",
            )
        self.assertGreater(checked, 1500)

    def test_candidate_keys_match_reference(self):
        rng = random.Random(7)
        for _ in range(2000):
            n = rng.randint(2, 5)
            attrs = frozenset("abcde"[:n])
            fds = random_fds(attrs, rng)
            if not fds:
                continue
            cover = nf_core.minimal_cover(fds)
            got = {frozenset(k) for k in nf_core.candidate_keys(attrs, cover)}
            expected = {frozenset(k) for k in keys_ref(attrs, fds)}
            self.assertEqual(
                got, expected,
                msg=f"keys mismatch attrs={sorted(attrs)} fds={sorted(str(f) for f in fds)}",
            )

    def test_minimal_cover_is_equivalent_and_minimal(self):
        rng = random.Random(99)
        for _ in range(2000):
            n = rng.randint(2, 5)
            attrs = frozenset("abcde"[:n])
            fds = random_fds(attrs, rng)
            if not fds:
                continue
            cover = nf_core.minimal_cover(fds)

            # 1) 等价性：对所有子集的闭包一致
            for x in all_subsets(attrs, 0):
                self.assertEqual(closure_ref(fds, x), closure_ref(cover, x))

            # 2) 右部单属性
            for fd in cover:
                self.assertEqual(len(fd.rhs), 1)

            # 3) 无左部多余属性
            for fd in cover:
                for attr in fd.lhs:
                    reduced = fd.lhs - {attr}
                    self.assertNotIn(fd.rhs, closure_ref(cover, reduced),
                                     msg=f"lhs extraneous in {fd}")

            # 4) 无冗余依赖
            for fd in cover:
                self.assertNotIn(fd.rhs, closure_ref(cover - {fd}, fd.lhs),
                                 msg=f"redundant fd {fd}")


class TestSchemaInjectionSafety(unittest.TestCase):
    def test_adding_declared_key_fds_never_lowers_nf(self):
        """只有当声明的键 K 在数据中确实成立(closure(K)=全体)时，注入 K->其余 才不会降低 NF。

        现实中 K 是被数据库强制的 PK/UNIQUE，成功 INSERT 即保证唯一、K 必为超键，
        所以注入是冗余/安全的。若 K 并非真正的超键(伪造的键)，注入反而会降低 NF——
        但这种键根本无法通过 INSERT 校验。
        """
        rank = {"1NF": 1, "2NF": 2, "3NF": 3, "BCNF": 4}
        rng = random.Random(1234)
        checked = 0
        for _ in range(3000):
            n = rng.randint(2, 5)
            attrs = frozenset("abcde"[:n])
            fds = random_fds(attrs, rng)
            if not fds or nf_core.analyze(attrs, fds)["nf"] == "NoFDs":
                continue

            key = frozenset(rng.sample(sorted(attrs), rng.randint(1, n)))
            # 只考虑"真的是数据中的超键"的声明键（数据库强制唯一的情形）
            if closure_ref(fds, key) != attrs:
                continue

            base = nf_core.analyze(attrs, fds)["nf"]
            schema = {FD(key, frozenset([a])) for a in attrs - key}
            injected = nf_core.analyze(attrs, fds | schema)["nf"]
            checked += 1
            self.assertGreaterEqual(
                rank[injected], rank[base],
                msg=f"NF dropped attrs={sorted(attrs)} fds={sorted(str(f) for f in fds)} key={sorted(key)} base={base} injected={injected}",
            )
        self.assertGreater(checked, 200)

    def test_bogus_declared_key_can_lower_nf(self):
        """反面用例：伪造的键(数据中不成立)注入后会降低 NF——说明必须由 DB 强制唯一。"""
        attrs = frozenset({"a", "b", "c", "d", "e"})
        fds = {FD(frozenset({"a", "b", "c"}), frozenset({"d", "e"})),
               FD(frozenset({"d", "e"}), frozenset({"a", "b"}))}
        base = nf_core.analyze(attrs, fds)["nf"]
        bogus = frozenset({"c"})  # c 在数据中并不是超键
        schema = {FD(bogus, frozenset([a])) for a in attrs - bogus}
        injected = nf_core.analyze(attrs, fds | schema)["nf"]
        self.assertEqual(base, "3NF")
        self.assertEqual(injected, "2NF")


if __name__ == "__main__":
    unittest.main()
