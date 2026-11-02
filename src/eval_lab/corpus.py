"""Small transparent lexical retrieval; no cloud search or embeddings."""
from __future__ import annotations
import hashlib
import json
import math
import os
import re
from collections import Counter
from pathlib import Path

DEFAULT_DATA = Path.cwd()/"data" if (Path.cwd()/"data"/"corpus.json").is_file() else Path(__file__).resolve().parents[2]/"data"
DATA_DIR = Path(os.environ.get("EVAL_LAB_DATA_DIR", DEFAULT_DATA))

def load_json(name: str):
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))

class Corpus:
    def __init__(self, payload: dict | None = None):
        self.payload = payload or load_json("corpus.json")
        self.documents = {d["id"]: d for d in self.payload["documents"]}
        self.passages = {p["id"]: p for d in self.documents.values() for p in d["passages"]}
        self.version = self.payload["version"]
        self.sha256 = hashlib.sha256(json.dumps(self.payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        self._terms = {pid: Counter(self._tokenize(p["label"] + " " + p["text"])) for pid,p in self.passages.items()}

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return re.findall(r"[a-z0-9]+", text.lower())

    def allowed_ids(self, allowed: list[str]) -> set[str]:
        return set(self.documents) if allowed == ["*"] else set(allowed) & self.documents.keys()

    def retrieve(self, passage_id: str, allowed: list[str]) -> dict:
        p = self.passages.get(passage_id)
        if p is None or p["document_id"] not in self.allowed_ids(allowed):
            raise ValueError("That passage is outside the evidence available for this case.")
        d = self.documents[p["document_id"]]
        return {**p, "source_url":d["source_url"], "document_date":d["date"],
            "archival_annotations":d.get("annotations",[]), "document_title":d["title"]}

    def search(self, query: str, allowed: list[str], limit: int = 5) -> list[dict]:
        tokens = self._tokenize(query)
        candidates = [(pid,terms) for pid,terms in self._terms.items()
            if self.passages[pid]["document_id"] in self.allowed_ids(allowed)]
        count = len(candidates)
        frequencies = {t:sum(t in terms for _,terms in candidates) for t in set(tokens)}
        def score(item):
            pid,terms = item
            size = max(sum(terms.values()),1)
            lexical = sum(math.log(1+(count+1)/(frequencies[t]+1))*terms[t]/(terms[t]+.5+size/200) for t in tokens)
            return lexical + (3 if query.strip().lower()==pid.lower() else 0)
        ranked = sorted(candidates,key=lambda item:(-score(item),item[0]))
        return [self.retrieve(pid,allowed) for pid,_ in ranked[:max(1,min(limit,8))]]

def cases() -> list[dict]:
    return load_json("cases.json")["cases"]

def case_by_id(case_id: str) -> dict:
    for case in cases():
        if case["id"] == case_id:
            return case
    raise ValueError(f"Unknown case: {case_id}")

