# -*- coding: utf-8 -*-
"""nf_core 正确性单元测试（stdlib unittest，无需 pytest）。

运行：
    python -m unittest tests.test_nf_core -v
"""
import unittest
from itertools import combinations

from normalizer_tool import nf_core
from normalizer_tool.fds import FD, parse_fd, fd_to_str


def F(text):
    return parse_fd(text)


def as_sets(keys):
    return {frozenset(k) for k in keys}


def closure_matches(original, cover):
    """验证 cover 与 original 对所有子集的闭包一致。"""
    attrs = set()
    for fd in original:
        attrs |= fd.lhs | fd.rhs
    for size in range(0, len(attrs) + 1):
        for combo in combinations(sorted(attrs), size):
            if nf_core.closure(original, combo) != nf_core.closure(cover, combo):
                return False
    return True


class TestClosureAndSuperkey(unittest.TestCase):
    def test_closure_basic(self):
        fds = {F("a -> b"), F("b -> c")}
        self.assertEqual(nf_core.closure(fds, {"a"}), frozenset({"a", "b", "c"}))
        self.assertEqual(nf_core.closure(fds, {"b"}), frozenset({"b", "c"}))

    def test_superkey(self):
        fds = {F("a -> b"), F("a -> c")}
        attrs = {"a", "b", "c"}
        self.assertTrue(nf_core.is_superkey(fds, attrs, {"a"}))
        self.assertTrue(nf_core.is_superkey(fds, attrs, {"a", "b"}))
        self.assertFalse(nf_core.is_superkey(fds, attrs, {"b"}))


class TestMinimalCover(unittest.TestCase):
    def test_reduce_and_singleton(self):
        fds = {F("a, b -> c"), F("a -> b"), F("a -> c")}
        cover = nf_core.minimal_cover(fds)
        self.assertEqual(cover, {F("a -> b"), F("a -> c")})
        self.assertTrue(closure_matches(fds, cover))

    def test_equivalence_and_determinism(self):
        fds = {F("a, b -> c"), F("c -> a"), F("a, c -> b")}
        first = nf_core.minimal_cover(fds)
        for _ in range(50):
            self.assertEqual(nf_core.minimal_cover(fds), first)
        self.assertTrue(closure_matches(fds, first))
        for fd in first:
            self.assertEqual(len(fd.rhs), 1)


class TestCandidateKeys(unittest.TestCase):
    def test_single_key(self):
        fds = {F("a -> b"), F("b -> c"), F("c -> d")}
        attrs = {"a", "b", "c", "d"}
        self.assertEqual(as_sets(nf_core.candidate_keys(attrs, fds)), {frozenset({"a"})})

    def test_multiple_keys(self):
        fds = {F("a, b -> c"), F("c -> a")}
        attrs = {"a", "b", "c"}
        keys = as_sets(nf_core.candidate_keys(attrs, fds))
        self.assertEqual(keys, {frozenset({"a", "b"}), frozenset({"b", "c"})})

    def test_attribute_never_in_rhs_must_be_in_key(self):
        fds = {F("a -> b")}
        attrs = {"a", "b", "c"}
        keys = as_sets(nf_core.candidate_keys(attrs, fds))
        self.assertEqual(keys, {frozenset({"a", "c"})})


class TestNormalForms(unittest.TestCase):
    def test_bcnf(self):
        attrs = {"a", "b", "c"}
        result = nf_core.analyze(attrs, {F("a -> b"), F("a -> c")})
        self.assertEqual(result["nf"], "BCNF")
        self.assertEqual(result["violations"], [])

    def test_3nf_but_not_bcnf(self):
        # 经典例子：键 {a,b} 与 {b,c}，c -> a 左部非超键但右部主属性
        attrs = {"a", "b", "c"}
        result = nf_core.analyze(attrs, {F("a, b -> c"), F("c -> a")})
        self.assertEqual(result["nf"], "3NF")
        self.assertTrue(any(v["level"] == "BCNF" for v in result["violations"]))
        self.assertFalse(any(v["level"] == "3NF" for v in result["violations"]))

    def test_2nf_transitive(self):
        attrs = {"a", "b", "c", "d"}
        result = nf_core.analyze(attrs, {F("a -> b"), F("b -> c"), F("c -> d")})
        self.assertEqual(result["nf"], "2NF")
        self.assertFalse(result["violations"][0]["level"] == "2NF")

    def test_1nf_partial_dependency(self):
        # 键 {a,b}，a -> c 是部分依赖，c 非主属性 => 1NF
        attrs = {"a", "b", "c"}
        result = nf_core.analyze(attrs, {F("a -> c"), F("b -> c")})
        self.assertEqual(result["nf"], "1NF")
        self.assertTrue(any(v["level"] == "2NF" for v in result["violations"]))

    def test_superkey_lhs_not_flagged_bcnf(self):
        # (a,c) -> b 的左部是超键（a 已是键），旧实现会误报 BCNF 违例
        attrs = {"a", "b", "c"}
        fds = {F("a -> b"), F("a -> c"), F("a, c -> b")}
        keys = nf_core.candidate_keys(attrs, nf_core.minimal_cover(fds))
        violations = nf_core.check_bcnf(attrs, nf_core.minimal_cover(fds), keys)
        self.assertEqual(violations, [])

    def test_no_fds(self):
        result = nf_core.analyze({"a", "b"}, set())
        self.assertEqual(result["nf"], "NoFDs")


class TestFDString(unittest.TestCase):
    def test_roundtrip_and_format(self):
        fd = parse_fd("b, a -> c")
        self.assertEqual(fd, FD(frozenset({"a", "b"}), frozenset({"c"})))
        self.assertEqual(fd_to_str(fd), "a, b -> c")


if __name__ == "__main__":
    unittest.main()
