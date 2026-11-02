#!/usr/bin/env python3
"""Rebuild the bounded founding-document corpus from pinned NARA snapshots.

Offline rebuild (default): python3 scripts/collect_corpus.py
Explicitly replace the snapshots: python3 scripts/collect_corpus.py --fetch

Only HTML layout whitespace, HTML entities and documented NARA editorial
footnote markers are normalized. Historical spelling, case and punctuation
are preserved. This script uses only the Python standard library.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "declaration": {
        "url": "https://www.archives.gov/founding-docs/declaration-transcript",
        "title": "Declaration of Independence: A Transcription",
    },
    "articles": {
        "url": "https://www.archives.gov/milestone-documents/articles-of-confederation",
        "title": "Articles of Confederation (1777)",
    },
    "constitution": {
        "url": "https://www.archives.gov/founding-docs/constitution-transcript",
        "title": "The Constitution of the United States: A Transcription",
    },
    "bill-of-rights": {
        "url": "https://www.archives.gov/founding-docs/bill-of-rights-transcript",
        "title": "The Bill of Rights: A Transcription",
    },
    "amendments-11-27": {
        "url": "https://www.archives.gov/founding-docs/amendments-11-27",
        "title": "The Constitution: Amendments 11-27",
    },
}
VERSION = "2026-11-02"
BR = "\ufff0"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class Block:
    tag: str
    text: str


class MainBlocks(HTMLParser):
    """Read the actual NARA main-content section, excluding menus and scripts."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.section_depth = 0
        self.active_tag: str | None = None
        self.parts: list[str] = []
        self.blocks: list[Block] = []
        self.ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "section":
            if self.section_depth:
                self.section_depth += 1
            elif attributes.get("id") == "block-system-main":
                self.section_depth = 1
        if not self.section_depth:
            return
        if tag in {"script", "style"}:
            self.ignored_depth += 1
        if not self.ignored_depth and tag in {"p", "h1", "h2", "h3", "h4"}:
            if self.active_tag:
                raise ValueError("Unexpected nested content block")
            self.active_tag = tag
            self.parts = []
        if tag == "br" and self.active_tag:
            self.parts.append(BR)

    def handle_endtag(self, tag: str) -> None:
        if self.section_depth and tag == self.active_tag:
            # Whitespace produced by HTML indentation is not primary text.
            lines = [re.sub(r"\s+", " ", line).strip() for line in "".join(self.parts).split(BR)]
            text = "\n".join(line for line in lines if line)
            if text:
                self.blocks.append(Block(tag, text))
            self.active_tag = None
            self.parts = []
        if self.section_depth and tag in {"script", "style"}:
            self.ignored_depth = max(0, self.ignored_depth - 1)
        if tag == "section" and self.section_depth:
            self.section_depth -= 1

    def handle_data(self, data: str) -> None:
        if self.section_depth and self.active_tag and not self.ignored_depth:
            self.parts.append(data)


def source_blocks(key: str) -> list[Block]:
    parser = MainBlocks()
    parser.feed((ROOT / "data" / "sources" / f"{key}.html").read_text(encoding="utf-8"))
    if not parser.blocks or parser.blocks[0].text != SOURCES[key]["title"]:
        raise ValueError(f"Source title changed or HTML extraction failed: {key}")
    return parser.blocks


def roman_number(text: str) -> int:
    values = {"I": 1, "V": 5, "X": 10, "L": 50}
    return sum(-values[c] if i + 1 < len(text) and values[c] < values[text[i + 1]]
               else values[c] for i, c in enumerate(text))


def provenance(key: str, manifest: dict, dates: dict[str, str] | None = None) -> dict:
    snapshot = manifest["sources"][key]
    return {
        "publisher": "U.S. National Archives and Records Administration",
        "source_title": SOURCES[key]["title"],
        "source_snapshot": f"data/sources/{key}.html",
        "retrieved_at": snapshot["retrieved_at"],
        "retrieved_date": snapshot["retrieved_at"][:10],
        "source_sha256": snapshot["sha256"],
        "text_encoding": "UTF-8",
        "extraction": "Complete designated NARA transcript; HTML entities decoded and layout whitespace normalized. Source notes and chronology stored in annotations. See data/sources/README.md.",
        "dates": dates or {},
    }


def document(doc_id: str, title: str, date: str, source_key: str, manifest: dict,
             text_parts: list[str], passages: list[dict], annotations: list[str],
             dates: dict[str, str] | None = None) -> dict:
    text = "\n\n".join(text_parts)
    return {
        "id": doc_id,
        "title": title,
        "date": date,
        "source_url": SOURCES[source_key]["url"],
        "provenance": provenance(source_key, manifest, dates),
        "text": text,
        "sha256": sha256(text.encode("utf-8")),
        "annotations": annotations,
        "passages": passages,
    }


def passage(doc_id: str, suffix: str, label: str, text: str, ordinal: int) -> dict:
    return {"id": f"{doc_id}.{suffix}", "document_id": doc_id,
            "label": label, "text": text, "ordinal": ordinal}


def declaration(manifest: dict) -> dict:
    blocks = source_blocks("declaration")
    start = next(i for i, b in enumerate(blocks) if b.text == "In Congress, July 4, 1776")
    end = next(i for i, b in enumerate(blocks) if b.text.startswith("Back to Main"))
    primary = blocks[start:end]
    passages = []
    signatures = False
    for b in primary:
        if b.text == "Georgia":
            signatures = True
        if signatures:
            suffix = f"signatures.p{sum('.signatures.' in p['id'] for p in passages) + 1}"
            label = "Declaration of Independence · signatures"
        else:
            suffix = f"p{sum('.signatures.' not in p['id'] for p in passages) + 1}"
            label = f"Declaration of Independence · paragraph {len(passages) + 1}"
        passages.append(passage("declaration", suffix, label, b.text, len(passages) + 1))
    return document("declaration", "Declaration of Independence", "1776-07-04", "declaration", manifest,
                    [b.text for b in primary], passages, [blocks[1].text],
                    {"adopted": "1776-07-04"})


def articles(manifest: dict) -> dict:
    blocks = source_blocks("articles")
    start = next(i for i, b in enumerate(blocks) if b.text == "Transcript") + 1
    primary = blocks[start:]
    passages = []
    article = 0
    article_roman = ""
    article_p = 0
    for b in primary:
        match = re.match(r"Article ([IVX]+)\.", b.text)
        if match:
            article_roman = match[1]
            article = roman_number(match[1])
            article_p = 0
        article_p += 1
        if b.text.startswith("And Whereas it hath pleased"):
            suffix, label = "attestation.p1", "Articles of Confederation · attestation"
        elif article:
            suffix = f"article-{article}.p{article_p}"
            label = f"Articles of Confederation · Article {article_roman} · paragraph {article_p}"
        else:
            suffix, label = "preamble.p1", "Articles of Confederation · preamble"
        passages.append(passage("articles", suffix, label, b.text, len(passages) + 1))
    notes = [blocks[1].text] + [b.text for b in blocks[4:13]]
    notes.append("Source completeness: the complete transcript on this NARA page ends with the closing attestation dated July 9, 1778. The page describes delegate signatures on the parchment but does not transcribe them; this corpus does not invent or substitute a signature list.")
    return document("articles", "Articles of Confederation", "1777-11-15", "articles", manifest,
                    [b.text for b in primary], passages, notes,
                    {"adopted": "1777-11-15", "ratified": "1781-03-01", "attestation": "1778-07-09"})


def constitution(manifest: dict) -> dict:
    blocks = source_blocks("constitution")
    start = next(i for i, b in enumerate(blocks) if b.text.startswith("We the People"))
    end = next(i for i, b in enumerate(blocks) if b.text.startswith("Back to Main"))
    primary = [b for b in blocks[start:end] if not b.text.startswith("For biographies of the non-signing")]
    source_notes = [b.text for b in blocks[start:end] if b.text.startswith("For biographies of the non-signing")]
    article = section = paragraph = 0
    article_roman = ""
    signing = False
    passages = []
    for b in primary:
        if match := re.fullmatch(r"Article\. ([IVX]+)\.", b.text):
            article_roman = match[1]
            article = roman_number(article_roman)
            section = paragraph = 0
            continue
        if match := re.fullmatch(r"Section\. (\d+)\.", b.text):
            section = int(match[1])
            paragraph = 0
            continue
        if b.text.startswith('The Word, "the,"'):
            signing = True
            paragraph = 0
        paragraph += 1
        if signing:
            suffix = f"attestation-signatures.p{paragraph}"
            label = "Constitution · attestation and signatures"
        elif not article:
            suffix, label = "preamble.p1", "Constitution · Preamble"
        else:
            suffix = f"article-{article}" + (f".section-{section}" if section else "") + f".p{paragraph}"
            label = f"Constitution · Article {article_roman}" + (f", Section {section}" if section else "") + f" · paragraph {paragraph}"
        passages.append(passage("constitution", suffix, label, b.text, len(passages) + 1))
    return document("constitution", "Constitution of the United States (1787 original)", "1787-09-17", "constitution", manifest,
                    [b.text for b in primary], passages, [blocks[1].text, *source_notes,
                    "Original 1787 text is retained, including clauses subsequently changed. Hyperlinks pointing to later amendments are source annotations, not substitutions in the primary text."],
                    {"signed": "1787-09-17"})


def proposal(manifest: dict) -> dict:
    blocks = source_blocks("bill-of-rights")
    start = next(i for i, b in enumerate(blocks) if b.text.startswith("Congress of the United States begun"))
    end = next(i for i, b in enumerate(blocks) if b.text == "Amendments 11-27")
    primary = blocks[start:end]
    ordinals = ["first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth", "tenth", "eleventh", "twelfth"]
    passages = []
    for b in primary:
        if match := re.match(r"Article the (\w+)\.\.\.", b.text):
            number = ordinals.index(match[1]) + 1
            suffix, label = f"article-{number}.p1", f"1789 proposal · Article the {match[1]} (proposed article {number})"
        elif b.text == "ATTEST," or b.text.startswith("Frederick Augustus Muhlenberg"):
            number = sum(".attestation." in p["id"] for p in passages) + 1
            suffix, label = f"attestation.p{number}", "1789 proposal · attestation"
        else:
            number = len(passages) + 1
            suffix, label = f"preamble.p{number}", f"1789 proposal · introductory paragraph {number}"
        passages.append(passage("amendments-proposal-1789", suffix, label, b.text, len(passages) + 1))
    notes = [b.text for b in blocks[1:start - 1]]
    notes.append("This document is the full congressional proposal of twelve articles dated September 25, 1789. It is distinct from the ten amendments ratified in 1791. Proposed Article 1 was not ratified; proposed Article 2 became Amendment XXVII in 1992; proposed Articles 3–12 became Amendments I–X in 1791.")
    return document("amendments-proposal-1789", "1789 Congressional Proposal of Twelve Amendments", "1789-09-25", "bill-of-rights", manifest,
                    [b.text for b in primary], passages, notes, {"proposed": "1789-09-25"})


def parse_english_date(text: str) -> str:
    return datetime.strptime(text.replace("Sept.", "September"), "%B %d, %Y").date().isoformat()


def amendments(manifest: dict) -> list[dict]:
    documents = []
    for source_key in ["bill-of-rights", "amendments-11-27"]:
        blocks = source_blocks(source_key)
        headings = [(i, roman_number(match[1])) for i, b in enumerate(blocks)
                    if (match := re.fullmatch(r"AMENDMENT ([IVX]+)", b.text, re.IGNORECASE))]
        for heading_index, (start, number) in enumerate(headings):
            end = headings[heading_index + 1][0] if heading_index + 1 < len(headings) else len(blocks)
            body = blocks[start + 1:end]
            doc_id = f"amendment-{number:02}"
            notes = []
            dates = {"proposed": "1789-09-25", "ratified": "1791-12-15"} if number <= 10 else {}
            text_parts = []
            passages = []
            section = paragraph = 0
            for b in body:
                if b.text.startswith(("Back to", "Amendments 11-27")):
                    continue
                if b.text.startswith(("Note:", "*", "Passed by Congress", "Originally proposed")):
                    notes.append(b.text)
                    if match := re.search(r"(?:Passed by Congress|Originally proposed) (.+? \d{1,2}, \d{4})\.", b.text):
                        dates["proposed"] = parse_english_date(match[1])
                    if match := re.search(r"Ratified (.+? \d{1,2}, \d{4})\.", b.text):
                        dates["ratified"] = parse_english_date(match[1])
                    continue
                if match := re.fullmatch(r"Section (\d+)\.", b.text):
                    section = int(match[1])
                    paragraph = 0
                    text_parts.append(b.text)
                    continue
                if b.tag != "p":
                    raise ValueError(f"Unexpected amendment body heading: {doc_id}: {b}")
                text = b.text
                if number == 12:
                    text = text.replace("[And if", "And if").replace("--]*", "--")
                if number == 14:
                    text = text.replace("age,*", "age,")
                paragraph += 1
                text_parts.append(text)
                suffix = (f"section-{section}." if section else "") + f"p{paragraph}"
                label = f"Amendment {number}" + (f", Section {section}" if section else "") + f" · paragraph {paragraph}"
                passages.append(passage(doc_id, suffix, label, text, len(passages) + 1))
            if number <= 10:
                notes.insert(0, "NARA: These amendments were ratified December 15, 1791, and form the Bill of Rights. They correspond to proposed Articles 3–12 of the 1789 congressional resolution; they are numbered here as ratified amendments, not proposal articles.")
            if number == 12:
                notes.append("Extraction: NARA's editorial square brackets and footnote asterisk marking the superseded presidential-selection clause were removed from primary text; the clause itself, including its punctuation and double hyphen, is retained. The source snapshot preserves the original display markup.")
            if number == 14:
                notes.append("Extraction: NARA's editorial footnote asterisk after ‘twenty-one years of age,’ was removed from primary text. The original age language remains, and the source's later-amendment note is recorded above.")
            if not dates.get("ratified"):
                raise ValueError(f"Missing ratification date: {doc_id}")
            documents.append(document(doc_id, f"Amendment {number}", dates["ratified"], source_key, manifest,
                                      text_parts, passages, notes, dates))
    return documents


def relationships() -> list[dict]:
    def rel(source: str, target: str, kind: str, description: str) -> dict:
        return {"source_document_id": source, "target_document_id": target,
                "kind": kind, "description": description}

    result = [
        rel("constitution", "articles", "succeeds", "The Constitution succeeded the Articles of Confederation as the United States' frame of government. Compare Articles VIII with Constitution Article I, Section 8 for the allocation of taxing power."),
        rel("amendments-proposal-1789", "constitution", "proposes-amendments", "Congress proposed twelve articles under Article V on September 25, 1789; proposal did not itself ratify them."),
    ]
    for number in range(1, 28):
        result.append(rel(f"amendment-{number:02}", "constitution", "amends", f"Ratified Amendment {number} forms part of the Constitution; its primary text is preserved separately from the original 1787 text."))
    for number in range(1, 11):
        result.append(rel("amendments-proposal-1789", f"amendment-{number:02}", "proposal-ratified", f"Proposed Article {number + 2} became Amendment {number} on December 15, 1791. The first ten ratified amendments form the Bill of Rights collection."))
    result.extend([
        rel("amendments-proposal-1789", "amendment-27", "proposal-ratified", "Proposed Article 2 became Amendment XXVII on May 7, 1992; proposed Article 1 remains unratified."),
        rel("amendment-17", "constitution", "modifies", "Amendment XVII modifies Article I, Section 3, replacing selection of Senators by state legislatures with election by the people and changing the vacancy procedure."),
        rel("amendment-21", "amendment-18", "repeals", "Amendment XXI, Section 1, explicitly repeals the eighteenth article of amendment. Amendment XVIII remains in the historical corpus."),
        rel("amendment-11", "constitution", "modifies", "Amendment XI modifies Article III, Section 2, concerning suits against States."),
        rel("amendment-12", "constitution", "supersedes-part", "Amendment XII supersedes a portion of Article II, Section 1, concerning presidential electors."),
        rel("amendment-13", "constitution", "supersedes-part", "Amendment XIII supersedes a portion of Article IV, Section 2."),
        rel("amendment-14", "constitution", "modifies", "Amendment XIV, Section 2, modifies Article I, Section 2, on apportionment."),
        rel("amendment-16", "constitution", "modifies", "Amendment XVI modifies Article I, Section 9, on direct taxes."),
        rel("amendment-20", "constitution", "modifies", "Amendment XX, Section 2, modifies Article I, Section 4, on the meeting of Congress."),
        rel("amendment-20", "amendment-12", "supersedes-part", "Amendment XX, Section 3, supersedes part of Amendment XII."),
        rel("amendment-25", "constitution", "affects", "Amendment XXV affects Article II, Section 1, concerning presidential succession and inability."),
        rel("amendment-26", "amendment-14", "modifies", "Amendment XXVI, Section 1, modifies Amendment XIV, Section 2, concerning voting age."),
    ])
    return result


def load_manifest(fetch: bool) -> dict:
    source_dir = ROOT / "data" / "sources"
    source_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = source_dir / "manifest.json"
    if fetch:
        manifest = {"schema_version": "1.0", "sources": {}}
        for key, source in SOURCES.items():
            request = urllib.request.Request(source["url"], headers={"User-Agent": "FoundingDocumentsEvaluationLab/1.0 (public archival research)"})
            with urllib.request.urlopen(request, timeout=60) as response:
                raw = response.read()
                final_url = response.url
            (source_dir / f"{key}.html").write_bytes(raw)
            manifest["sources"][key] = {"source_url": source["url"], "final_url": final_url,
                "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "snapshot": f"data/sources/{key}.html", "sha256": sha256(raw), "bytes": len(raw)}
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for key, source in SOURCES.items():
        raw = (source_dir / f"{key}.html").read_bytes()
        record = manifest["sources"][key]
        if record["source_url"] != source["url"] or sha256(raw) != record["sha256"] or len(raw) != record["bytes"]:
            raise ValueError(f"Source snapshot integrity check failed: {key}")
    return manifest


def build(manifest: dict) -> dict:
    documents = [declaration(manifest), articles(manifest), constitution(manifest), proposal(manifest), *amendments(manifest)]
    expected = ["declaration", "articles", "constitution", "amendments-proposal-1789"] + [f"amendment-{n:02}" for n in range(1, 28)]
    if [d["id"] for d in documents] != expected:
        raise ValueError("Corpus must contain exactly the 31 declared document records in order")
    if len({d["sha256"] for d in documents}) != 31:
        raise ValueError("Duplicate primary document text")
    return {"schema_version": "1.0", "version": VERSION, "documents": documents,
            "collections": [{"id": "bill-of-rights", "title": "Bill of Rights",
                             "document_ids": [f"amendment-{n:02}" for n in range(1, 11)]}],
            "relationships": relationships()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", action="store_true", help="Explicitly replace all five source snapshots from archives.gov before rebuilding")
    args = parser.parse_args()
    corpus = build(load_manifest(args.fetch))
    (ROOT / "data" / "corpus").mkdir(parents=True, exist_ok=True)
    for doc in corpus["documents"]:
        (ROOT / "data" / "corpus" / f"{doc['id']}.txt").write_text(doc["text"], encoding="utf-8")
    (ROOT / "data" / "corpus.json").write_text(json.dumps(corpus, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Built {len(corpus['documents'])} documents, {sum(len(d['passages']) for d in corpus['documents'])} passages, {len(corpus['relationships'])} relationships from five verified NARA snapshots.")


if __name__ == "__main__":
    main()
