# -*- coding: utf-8 -*-
"""analyzer / decomposer 集成测试（不需要数据库）。

运行：
    python -m unittest tests.test_analyzer -v
"""
import json
import unittest

from normalizer_tool.analyzer import analyze_relation
from normalizer_tool.decomposer import propose
from normalizer_tool import nf_core
from normalizer_tool.fds import parse_fd


def F(text):
    return parse_fd(text)


class TestAnalyzeRelation(unittest.TestCase):
    def test_passed_bcnf(self):
        report = analyze_relation(
            {"a", "b", "c"}, {F("a -> b"), F("a -> c")}, target_nf="BCNF"
        )
        self.assertTrue(report["passed"])
        self.assertEqual(report["current_nf"], "BCNF")
        self.assertEqual(report["violations"], [])
        self.assertNotIn("decomposition", report)

    def test_failed_includes_violations_and_decomposition(self):
        report = analyze_relation(
            {"a", "b", "c", "d"},
            {F("a -> b"), F("b -> c"), F("c -> d")},
            target_nf="BCNF",
        )
        self.assertFalse(report["passed"])
        self.assertEqual(report["current_nf"], "2NF")
        self.assertTrue(report["violations"])
        self.assertIn("decomposition", report)

    def test_json_serializable(self):
        report = analyze_relation(
            {"a", "b", "c"}, {F("a -> c"), F("b -> c")}, target_nf="3NF"
        )
        json.dumps(report, ensure_ascii=False)
        self.assertFalse(report["passed"])

    def test_no_fds_warns(self):
        report = analyze_relation({"a", "b"}, set(), target_nf="BCNF")
        self.assertEqual(report["current_nf"], "NoFDs")
        self.assertTrue(report["warnings"])


class TestSchemaInjection(unittest.TestCase):
    def test_schema_fds_used_when_data_empty(self):
        # 数据没挖到 FD，但 schema 声明了主键 a => 仍能判定出 BCNF
        report = analyze_relation(
            {"a", "b", "c"},
            set(),
            target_nf="BCNF",
            schema_fds={F("a -> b"), F("a -> c")},
            declared_keys=[["a"]],
        )
        self.assertEqual(report["current_nf"], "BCNF")
        self.assertTrue(report["passed"])
        self.assertIn("a -> b", report["fd_sources"]["from_schema"])
        self.assertEqual(report["declared_keys"], [["a"]])

    def test_union_is_judged(self):
        # 数据给 a->b，schema 给 (a,b)->c；并集用于判定
        report = analyze_relation(
            {"a", "b", "c"},
            {F("a -> b")},
            target_nf="BCNF",
            schema_fds={F("a, b -> c")},
        )
        self.assertIn("a -> b", report["fd_sources"]["from_data"])
        self.assertIn("a, b -> c", report["fd_sources"]["from_schema"])
        self.assertIn("a -> b", report["fds"])

    def test_policy_data_ignores_schema(self):
        # 数据只有 a->b（此时 b 非主，违反 3NF => 2NF）；
        # schema 声明 b 为唯一键(b->a, b->c)，使 b 成为主属性/超键，违例消失 => BCNF
        data = {F("a -> b")}
        schema = {F("b -> a"), F("b -> c")}
        union = analyze_relation({"a", "b", "c"}, data, target_nf="BCNF", schema_fds=schema)
        data_only = analyze_relation(
            {"a", "b", "c"}, data, target_nf="BCNF", schema_fds=schema, fd_policy="data"
        )
        self.assertEqual(union["current_nf"], "BCNF")
        self.assertTrue(union["passed"])
        self.assertEqual(data_only["current_nf"], "1NF")
        self.assertFalse(data_only["passed"])

    def test_low_confidence_flag(self):
        report = analyze_relation(
            {"a", "b", "c"},
            {F("a -> c"), F("b -> c")},
            target_nf="3NF",
            support={F("a -> c"): 2, F("b -> c"): 5},
        )
        flagged = {item["fd"] for item in report["low_confidence_data_fds"]}
        self.assertIn("a -> c", flagged)
        self.assertNotIn("b -> c", flagged)


class TestDecomposer(unittest.TestCase):
    def test_bcnf_decomposition_all_fragments_bcnf(self):
        attrs = {"a", "b", "c", "d"}
        fds = {F("a -> b"), F("b -> c"), F("c -> d")}
        cover = nf_core.minimal_cover(fds)
        frags = propose(attrs, cover, fds, target="BCNF")
        self.assertTrue(frags)
        for frag in frags:
            self.assertEqual(frag["nf"], "BCNF", msg=f"fragment not BCNF: {frag}")

    def test_3nf_decomposition(self):
        attrs = {"a", "b", "c"}
        fds = {F("a, b -> c"), F("c -> a")}
        cover = nf_core.minimal_cover(fds)
        frags = propose(attrs, cover, fds, target="3NF")
        self.assertTrue(frags)
        for frag in frags:
            self.assertIn(frag["nf"], ("3NF", "BCNF"))


if __name__ == "__main__":
    unittest.main()
