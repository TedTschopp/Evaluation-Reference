"""Validate authored teaching assets; SDK evaluation is performed by the engine.

The small contract check below validates the intended fixture matrix. It is
not a substitute for LocalEvaluator and does not manufacture replay scores.
"""

import json
import re
import unittest
from collections import Counter
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CASE_IDS = [
    "proposed-1789", "ratified-1791", "senate-1789", "senate-1914",
    "prohibition-1925", "prohibition-1935", "tax-articles", "tax-constitution",
    "evidence-restricted", "evidence-restored", "ambiguity", "clear-context",
]
CASE_FIELDS = {
    "id", "family", "title", "question", "expected_behavior",
    "allowed_document_ids", "required_document_ids", "concepts",
    "expected_disposition", "as_of", "critical", "reference_answer",
    "reference_passage_ids",
}
ANSWER_FIELDS = {
    "case_id", "text", "citations", "disposition", "as_of", "retrieved_passage_ids",
}


class CaseAssetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.case_asset = json.loads((ROOT / "data/cases.json").read_text(encoding="utf-8"))
        cls.seed_asset = json.loads((ROOT / "data/fixture-seeds.json").read_text(encoding="utf-8"))
        cls.cases = {c["id"]: c for c in cls.case_asset["cases"]}
        cls.profiles = {p["id"]: p for p in cls.seed_asset["profiles"]}
        corpus = json.loads((ROOT / "data/corpus.json").read_text(encoding="utf-8"))
        cls.docs = {d["id"]: d for d in corpus["documents"]}
        cls.passages = {p["id"]: p for d in cls.docs.values() for p in d["passages"]}

    @classmethod
    def authored_contract_matches(cls, answer):
        """Check finite authored expectations, without claiming semantic proof."""
        case = cls.cases[answer["case_id"]]
        citations = set(answer["citations"])
        retrieved = set(answer["retrieved_passage_ids"])
        if answer["disposition"] != case["expected_disposition"] or answer["as_of"] != case["as_of"]:
            return False
        if not all(re.search(pattern, answer["text"]) for pattern in case["concepts"]):
            return False
        if not citations <= retrieved:
            return False
        allowed = set(cls.docs) if case["allowed_document_ids"] == ["*"] else set(case["allowed_document_ids"])
        if any(cls.passages[pid]["document_id"] not in allowed for pid in retrieved | citations):
            return False
        cited_docs = {cls.passages[pid]["document_id"] for pid in citations}
        if not set(case["required_document_ids"]) <= cited_docs:
            return False
        if case["expected_disposition"] == "answer" and not citations.intersection(case["reference_passage_ids"]):
            return False
        if case["as_of"] and any(cls.docs[cls.passages[pid]["document_id"]]["date"] > case["as_of"] for pid in citations):
            return False
        return True

    def test_twelve_cases_in_six_paired_families(self):
        self.assertEqual(self.case_asset["schema_version"], "1.0")
        self.assertEqual(self.case_asset["version"], "1.0.0")
        self.assertEqual([c["id"] for c in self.case_asset["cases"]], CASE_IDS)
        self.assertEqual(len(self.cases), 12)
        self.assertEqual(len(Counter(c["family"] for c in self.cases.values())), 6)
        self.assertEqual(set(Counter(c["family"] for c in self.cases.values()).values()), {2})
        self.assertEqual([c["id"] for c in self.cases.values() if c["critical"]], ["ratified-1791"])

    def test_case_schemas_dates_patterns_and_reference_answers(self):
        for case in self.cases.values():
            with self.subTest(case=case["id"]):
                self.assertEqual(set(case), CASE_FIELDS)
                for field in ["id", "family", "title", "question", "expected_behavior", "reference_answer"]:
                    self.assertTrue(case[field].strip())
                self.assertIn(case["expected_disposition"], {"answer", "clarify", "insufficient_evidence"})
                self.assertIsInstance(case["critical"], bool)
                if case["as_of"] is not None:
                    self.assertEqual(date.fromisoformat(case["as_of"]).isoformat(), case["as_of"])
                self.assertGreater(len(case["concepts"]), 0)
                for pattern in case["concepts"]:
                    compiled = re.compile(pattern)
                    self.assertIsNotNone(compiled.search(case["reference_answer"]))

    def test_all_case_document_and_passage_references_are_real_and_allowed(self):
        for case in self.cases.values():
            allowed = case["allowed_document_ids"]
            self.assertTrue(allowed)
            self.assertTrue(allowed == ["*"] or set(allowed) <= self.docs.keys())
            self.assertTrue(set(case["required_document_ids"]) <= self.docs.keys())
            allowed_set = set(self.docs) if allowed == ["*"] else set(allowed)
            self.assertTrue(set(case["required_document_ids"]) <= allowed_set)
            for pid in case["reference_passage_ids"]:
                self.assertIn(pid, self.passages)
                self.assertIn(self.passages[pid]["document_id"], allowed_set)
            if case["expected_disposition"] == "answer":
                self.assertTrue(case["reference_passage_ids"])
            else:
                self.assertEqual(case["reference_passage_ids"], [])

    def test_three_complete_authored_profiles_without_precomputed_scores(self):
        self.assertEqual(self.seed_asset["schema_version"], "1.0")
        self.assertIn("Authored teaching fixtures, not model outputs", self.seed_asset["provenance"])
        self.assertIn("Microsoft LocalEvaluator", self.seed_asset["provenance"])
        self.assertEqual([p["id"] for p in self.seed_asset["profiles"]], ["baseline", "candidate", "revised"])
        self.assertEqual(len(self.profiles), 3)
        for profile in self.profiles.values():
            self.assertEqual(set(profile), {"id", "title", "description", "answers"})
            self.assertTrue(profile["title"])
            self.assertTrue(profile["description"])
            self.assertEqual([a["case_id"] for a in profile["answers"]], CASE_IDS)
            for answer in profile["answers"]:
                self.assertEqual(set(answer), ANSWER_FIELDS)

    def test_all_seed_structured_responses_ids_dates_and_retrievals(self):
        all_answers = [a for p in self.profiles.values() for a in p["answers"]] + self.seed_asset["calibration"]
        for answer in all_answers:
            with self.subTest(case=answer["case_id"], calibration=answer.get("id")):
                self.assertIn(answer["case_id"], self.cases)
                case = self.cases[answer["case_id"]]
                self.assertEqual(answer["as_of"], case["as_of"])
                self.assertIn(answer["disposition"], {"answer", "clarify", "insufficient_evidence"})
                self.assertTrue(answer["text"].strip())
                self.assertEqual(len(answer["citations"]), len(set(answer["citations"])))
                self.assertEqual(len(answer["retrieved_passage_ids"]), len(set(answer["retrieved_passage_ids"])))
                for pid in answer["citations"] + answer["retrieved_passage_ids"]:
                    self.assertIn(pid, self.passages)
                if answer.get("id") != "right-answer-wrong-citation":
                    self.assertTrue(set(answer["citations"]) <= set(answer["retrieved_passage_ids"]))

    def test_authored_expected_pass_matrix(self):
        expected_failures = {
            "baseline": {"senate-1789", "prohibition-1935", "tax-articles", "ambiguity"},
            "candidate": {"ratified-1791"},
            "revised": set(),
        }
        for profile_id, profile in self.profiles.items():
            failures = {a["case_id"] for a in profile["answers"] if not self.authored_contract_matches(a)}
            self.assertEqual(failures, expected_failures[profile_id])
        self.assertEqual([sum(self.authored_contract_matches(a) for a in self.profiles[pid]["answers"])
                          for pid in ["baseline", "candidate", "revised"]], [8, 11, 12])

    def test_candidate_failure_is_the_single_critical_gate(self):
        answers = self.profiles["candidate"]["answers"]
        failed_critical = [a["case_id"] for a in answers
                           if self.cases[a["case_id"]]["critical"] and not self.authored_contract_matches(a)]
        self.assertEqual(failed_critical, ["ratified-1791"])
        wrong = next(a for a in answers if a["case_id"] == "ratified-1791")
        self.assertIn("Twelve", wrong["text"])
        self.assertEqual(wrong["citations"], ["amendments-proposal-1789.article-12.p1"])

    def test_eight_calibrations_have_expected_bounded_results(self):
        expected_ids = [
            "correct-paraphrase", "correct-words-wrong-era", "right-answer-wrong-citation",
            "unsupported-memory-guess", "justified-insufficiency", "unnecessary-clarification",
            "wrong-12-ratified", "correct-12-proposed",
        ]
        calibration = self.seed_asset["calibration"]
        self.assertEqual([c["id"] for c in calibration], expected_ids)
        for item in calibration:
            self.assertEqual(set(item), ANSWER_FIELDS | {"id", "label", "expected_pass", "explanation"})
            self.assertTrue(item["label"])
            self.assertTrue(item["explanation"])
            self.assertIsInstance(item["expected_pass"], bool)
            self.assertEqual(self.authored_contract_matches(item), item["expected_pass"], item["id"])
        self.assertEqual(sum(c["expected_pass"] for c in calibration), 3)

    def test_exactly_one_intentional_provenance_failure(self):
        failures = [c["id"] for c in self.seed_asset["calibration"]
                    if not set(c["citations"]) <= set(c["retrieved_passage_ids"])]
        self.assertEqual(failures, ["right-answer-wrong-citation"])
        item = next(c for c in self.seed_asset["calibration"] if c["id"] == failures[0])
        self.assertEqual(item["citations"], ["constitution.article-1.section-8.p1"])
        self.assertEqual(item["retrieved_passage_ids"], ["constitution.article-1.section-3.p1"])

    def test_restricted_and_restored_evidence_pair(self):
        restricted = self.cases["evidence-restricted"]
        restored = self.cases["evidence-restored"]
        self.assertEqual(restricted["allowed_document_ids"], ["declaration"])
        self.assertEqual(restricted["expected_disposition"], "insufficient_evidence")
        self.assertEqual(restored["allowed_document_ids"], ["constitution"])
        self.assertEqual(restored["expected_disposition"], "answer")
        for profile in self.profiles.values():
            answer = next(a for a in profile["answers"] if a["case_id"] == "evidence-restricted")
            self.assertEqual(answer["citations"], [])
            self.assertEqual(answer["retrieved_passage_ids"], ["declaration.p3"])

    def test_count_references_expose_nara_chronology(self):
        for case_id, phrase in [("proposed-1789", "proposed 12 amendments"),
                                ("ratified-1791", "ratified December 15, 1791")]:
            case = self.cases[case_id]
            notes = [note for pid in case["reference_passage_ids"]
                     for note in self.docs[self.passages[pid]["document_id"]]["annotations"]]
            self.assertTrue(any(phrase in note for note in notes))


if __name__ == "__main__":
    unittest.main()
