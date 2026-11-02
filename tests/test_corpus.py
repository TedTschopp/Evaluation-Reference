"""Source fidelity and structural safeguards for the curated primary corpus."""

import hashlib
from html import unescape
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_IDS = ["declaration", "articles", "constitution", "amendments-proposal-1789"] + [
    f"amendment-{number:02}" for number in range(1, 28)
]


class CorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus = json.loads((ROOT / "data/corpus.json").read_text(encoding="utf-8"))
        cls.docs = {doc["id"]: doc for doc in cls.corpus["documents"]}
        cls.passages = {p["id"]: p for d in cls.docs.values() for p in d["passages"]}
        cls.manifest = json.loads((ROOT / "data/sources/manifest.json").read_text(encoding="utf-8"))

    def test_exactly_31_unique_records_and_no_bill_of_rights_duplicate(self):
        self.assertEqual(self.corpus["schema_version"], "1.0")
        self.assertEqual(self.corpus["version"], "2026-11-02")
        self.assertEqual([d["id"] for d in self.corpus["documents"]], EXPECTED_IDS)
        self.assertEqual(len(self.docs), 31)
        self.assertEqual(len({d["sha256"] for d in self.docs.values()}), 31)
        self.assertNotIn("bill-of-rights", self.docs)
        self.assertEqual(self.corpus["collections"], [{
            "id": "bill-of-rights", "title": "Bill of Rights",
            "document_ids": [f"amendment-{n:02}" for n in range(1, 11)],
        }])

    def test_all_text_checksums_and_files_match(self):
        files = sorted(path.stem for path in (ROOT / "data/corpus").glob("*.txt"))
        self.assertEqual(files, sorted(EXPECTED_IDS))
        for doc_id, doc in self.docs.items():
            with self.subTest(document=doc_id):
                data = doc["text"].encode("utf-8")
                self.assertEqual(hashlib.sha256(data).hexdigest(), doc["sha256"])
                self.assertEqual((ROOT / "data/corpus" / f"{doc_id}.txt").read_bytes(), data)
                self.assertNotIn("\ufffd", doc["text"])
                self.assertNotIn("<p>", doc["text"])

    def test_authoritative_source_snapshots_and_provenance(self):
        expected_urls = {
            "https://www.archives.gov/founding-docs/declaration-transcript",
            "https://www.archives.gov/milestone-documents/articles-of-confederation",
            "https://www.archives.gov/founding-docs/constitution-transcript",
            "https://www.archives.gov/founding-docs/bill-of-rights-transcript",
            "https://www.archives.gov/founding-docs/amendments-11-27",
        }
        self.assertEqual({d["source_url"] for d in self.docs.values()}, expected_urls)
        self.assertEqual(len(self.manifest["sources"]), 5)
        for snapshot in self.manifest["sources"].values():
            raw = (ROOT / snapshot["snapshot"]).read_bytes()
            self.assertEqual(len(raw), snapshot["bytes"])
            self.assertGreater(len(raw), 40_000)
            self.assertEqual(hashlib.sha256(raw).hexdigest(), snapshot["sha256"])
            self.assertIn(snapshot["source_url"], expected_urls)
            self.assertRegex(snapshot["retrieved_at"], r"^2026-11-02T")
        for doc in self.docs.values():
            meta = doc["provenance"]
            raw = (ROOT / meta["source_snapshot"]).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), meta["source_sha256"])
            self.assertEqual(meta["retrieved_date"], "2026-11-02")
            self.assertIn("National Archives", meta["publisher"])

    def test_passage_ids_ownership_ordinals_and_text_coverage(self):
        all_passages = [p for doc in self.docs.values() for p in doc["passages"]]
        self.assertEqual(len(self.passages), len(all_passages))
        for doc in self.docs.values():
            self.assertEqual([p["ordinal"] for p in doc["passages"]], list(range(1, len(doc["passages"]) + 1)))
            for p in doc["passages"]:
                self.assertEqual(p["document_id"], doc["id"])
                self.assertTrue(p["id"].startswith(doc["id"] + "."))
                self.assertIn(p["text"], doc["text"])
                self.assertTrue(p["label"])
            # All prose and signatures occur in passages. Only actual structural
            # article/section headings are excluded as stand-alone passages.
            without_headings = [block for block in doc["text"].split("\n\n")
                                if not re.fullmatch(r"(?:Article\. [IVX]+\.|Section\.? \d+\.)", block)]
            self.assertEqual(without_headings, [p["text"] for p in doc["passages"]])

    def test_complete_documents_include_final_articles_and_attestations(self):
        declaration = self.docs["declaration"]["text"]
        self.assertTrue(declaration.startswith("In Congress, July 4, 1776"))
        self.assertIn("our Lives, our Fortunes and our sacred Honor.", declaration)
        self.assertTrue(declaration.endswith("Matthew Thornton"))
        self.assertIn("Brittish brethren", declaration)
        self.assertIn("compleat the works of death", declaration)
        articles = self.docs["articles"]["text"]
        self.assertGreater(len(articles), 20_000)
        self.assertIn("Article XIII. Every State shall abide", articles)
        self.assertIn("con-firmed by the legislatures of every state", articles)
        self.assertTrue(articles.endswith("in the third year of the Independence of America."))
        self.assertTrue(any("does not transcribe" in note for note in self.docs["articles"]["annotations"]))
        constitution = self.docs["constitution"]["text"]
        self.assertGreater(len(constitution), 27_000)
        self.assertIn("Article. VII.", constitution)
        self.assertIn('The Word, "the," being interlined', constitution)
        self.assertIn("Attest William Jackson Secretary", constitution)
        self.assertTrue(constitution.endswith("Gouv Morris"))
        self.assertIn("Independance", constitution)

    def test_true_article_and_section_structure(self):
        articles = self.docs["articles"]["passages"]
        self.assertEqual({int(re.search(r"\.article-(\d+)\.", p["id"])[1]) for p in articles if ".article-" in p["id"]}, set(range(1, 14)))
        constitutional = self.docs["constitution"]["passages"]
        self.assertEqual({int(re.search(r"\.article-(\d+)\.", p["id"])[1]) for p in constitutional if ".article-" in p["id"]}, set(range(1, 8)))
        self.assertIn("constitution.article-1.section-10.p3", self.passages)
        self.assertIn("constitution.article-2.section-4.p1", self.passages)
        self.assertIn("constitution.article-3.section-3.p2", self.passages)
        self.assertIn("constitution.article-4.section-4.p1", self.passages)
        self.assertIn("constitution.article-5.p1", self.passages)
        self.assertIn("constitution.article-6.p3", self.passages)
        self.assertIn("constitution.article-7.p1", self.passages)
        sections = {13: 2, 14: 5, 15: 2, 18: 3, 20: 6, 21: 3,
                    22: 2, 23: 2, 24: 2, 25: 4, 26: 2}
        for number, count in sections.items():
            for section in range(1, count + 1):
                self.assertIn(f"amendment-{number:02}.section-{section}.p1", self.passages)
        self.assertIn("amendment-25.section-4.p2", self.passages)
        self.assertIn("amendment-23.section-1.p2", self.passages)

    def test_1789_proposal_has_12_articles_distinct_from_10_ratifications(self):
        doc = self.docs["amendments-proposal-1789"]
        self.assertEqual(len([p for p in doc["passages"] if ".article-" in p["id"]]), 12)
        first = self.passages["amendments-proposal-1789.article-1.p1"]["text"]
        self.assertIn("not be less than two hundred Representatives", first)
        second = self.passages["amendments-proposal-1789.article-2.p1"]["text"]
        self.assertIn(self.docs["amendment-27"]["text"], second)
        third = self.passages["amendments-proposal-1789.article-3.p1"]["text"]
        self.assertIn(self.docs["amendment-01"]["text"], third)
        self.assertIn("ATTEST,", doc["text"])
        self.assertTrue(doc["text"].endswith("Sam. A Otis Secretary of the Senate"))
        self.assertEqual(doc["date"], "1789-09-25")
        for number in range(1, 11):
            self.assertEqual(self.docs[f"amendment-{number:02}"]["date"], "1791-12-15")
        self.assertEqual(self.docs["amendment-27"]["date"], "1992-05-07")

    def test_original_senate_selection_and_17th_amendment(self):
        original = self.passages["constitution.article-1.section-3.p1"]["text"]
        later = self.passages["amendment-17.p1"]["text"]
        self.assertIn("chosen by the Legislature", original)
        self.assertIn("elected by the people", later)
        self.assertNotIn("elected by the people", original)
        self.assertIn("vacancies by election", self.passages["amendment-17.p2"]["text"])

    def test_18th_is_retained_and_21st_repeal_explicit(self):
        self.assertIn("intoxicating liquors", self.passages["amendment-18.section-1.p1"]["text"])
        self.assertEqual(self.passages["amendment-21.section-1.p1"]["text"],
                         "The eighteenth article of amendment to the Constitution of the United States is hereby repealed.")
        self.assertTrue(any(rel["kind"] == "repeals" and rel["source_document_id"] == "amendment-21" and rel["target_document_id"] == "amendment-18" for rel in self.corpus["relationships"]))

    def test_tax_power_comparison_passages(self):
        earlier = self.passages["articles.article-8.p1"]["text"]
        later = self.passages["constitution.article-1.section-8.p1"]["text"]
        self.assertIn("common treasury", earlier)
        self.assertIn("laid and levied by the authority and direction of the legislatures of the several states", earlier)
        self.assertIn("The Congress shall have Power To lay and collect Taxes", later)

    def test_archival_notes_do_not_contaminate_primary_text(self):
        for doc in self.docs.values():
            for phrase in ["Note:", "Passed by Congress", "Ratified February", "For biographies", "Back to Main", "*Superseded", "*Changed"]:
                self.assertNotIn(phrase, doc["text"])
        twelfth = self.docs["amendment-12"]
        self.assertIn("And if the House of Representatives shall not choose a President", twelfth["text"])
        self.assertNotIn("[", twelfth["text"])
        self.assertNotIn("]", twelfth["text"])
        self.assertNotIn("*", twelfth["text"])
        self.assertTrue(any("Superseded by section 3" in note for note in twelfth["annotations"]))
        fourteenth = self.docs["amendment-14"]
        self.assertIn("twenty-one years of age,", fourteenth["text"])
        self.assertNotIn("*", fourteenth["text"])
        self.assertTrue(any("Changed by section 1" in note for note in fourteenth["annotations"]))

    def test_relationships_reference_real_documents(self):
        for rel in self.corpus["relationships"]:
            self.assertIn(rel["source_document_id"], self.docs)
            self.assertIn(rel["target_document_id"], self.docs)
            self.assertTrue(rel["description"])

    def test_entire_source_transcripts_match_without_omitted_text(self):
        # This independent raw-HTML comparison does not import the collector or
        # use its block parser. It checks every non-layout character in each
        # supplied transcript, including the end of every document.
        def compact_html(raw):
            raw = re.sub(r"<!--.*?-->", "", raw, flags=re.DOTALL)
            return re.sub(r"\s+", "", unescape(re.sub(r"<[^>]*>", "", raw)))

        def compact_text(text):
            return re.sub(r"\s+", "", text)

        bounds = {
            "declaration": ('<p class="larger"><strong>In Congress, July 4, 1776', '<p><a class="btn btn-default active" href="/founding-docs/declaration"'),
            "articles": ('<p>To all to whom these Presents shall come', '</div>'),
            "constitution": ('<p><span class="larger"><strong>We the People', '<p>For biographies of the non-signing'),
            "amendments-proposal-1789": ('<p>Congress of the United States begun', '<p><a class="btn btn-default active" href="/founding-docs/amendments-11-27"'),
        }
        for doc_id, (start, end) in bounds.items():
            snapshot = ROOT / self.docs[doc_id]["provenance"]["source_snapshot"]
            raw = snapshot.read_text(encoding="utf-8")
            raw = raw[raw.index(start):]
            raw = raw[:raw.index(end)]
            with self.subTest(document=doc_id):
                self.assertEqual(compact_html(raw), compact_text(self.docs[doc_id]["text"]))

        for key, heading_pattern in [
            ("bill-of-rights", r"<h3>Amendment ([IVX]+)</h3>"),
            ("amendments-11-27", r"<h[23][^>]*>(?:(?!</h[23]>).)*?AMENDMENT ([IVX]+)</h[23]>"),
        ]:
            raw = (ROOT / f"data/sources/{key}.html").read_text(encoding="utf-8")
            headings = list(re.finditer(heading_pattern, raw, flags=re.DOTALL))
            first_number = 1 if key == "bill-of-rights" else 11
            self.assertEqual(len(headings), 10 if first_number == 1 else 17)
            for index, heading in enumerate(headings):
                number = first_number + index
                end = headings[index + 1].start() if index + 1 < len(headings) else raw.index('<p><a class="btn btn-default active', heading.end())
                body = raw[heading.end():end]

                def omit_editorial_paragraph(match):
                    text = compact_html(match[0])
                    return "" if text.startswith(("Note:", "*", "PassedbyCongress", "Originallyproposed")) else match[0]

                body = re.sub(r"<p\b[^>]*>.*?</p>", omit_editorial_paragraph, body, flags=re.DOTALL)
                source_text = compact_html(body)
                if number == 12:
                    source_text = source_text.replace("[Andif", "Andif").replace("--]*", "--")
                if number == 14:
                    source_text = source_text.replace("age,*", "age,")
                with self.subTest(document=f"amendment-{number:02}"):
                    self.assertEqual(source_text, compact_text(self.docs[f"amendment-{number:02}"]["text"]))

    def test_offline_rebuild_is_byte_identical(self):
        before = (ROOT / "data/corpus.json").read_bytes()
        result = subprocess.run([sys.executable, str(ROOT / "scripts/collect_corpus.py")], cwd=ROOT,
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(before, (ROOT / "data/corpus.json").read_bytes())


if __name__ == "__main__":
    unittest.main()
