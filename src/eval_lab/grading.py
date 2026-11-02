"""Transparent task checks executed by the real Microsoft LocalEvaluator."""
from __future__ import annotations
import dataclasses
import json
import re
from agent_framework import CheckResult, EvalItem, LocalEvaluator, Message, evaluator
from .corpus import Corpus
from .models import AgentAnswer, Grade

LABELS = {
    "task_intent":"Task meaning", "citation_provenance":"Citation provenance",
    "evidence_boundary":"Evidence boundary", "scope_alignment":"Document and time scope",
    "appropriate_response":"Answer or ask appropriately", "source_value_match":"Weak source-overlap checker",
}
CRITERIA_NOTE = "These finite case-specific checks are inspectable heuristics, not a general proof of semantic correctness."

def result_status(grades: list[Grade]) -> str:
    required = [g for g in grades if g.required]
    if any(g.status == "fail" for g in required):
        return "fail"
    if any(g.status in {"error","not_assessed"} for g in required):
        return "unresolved"
    return "fail" if any(g.status=="fail" for g in required) else "pass"

async def grade_answer(case: dict, answer: AgentAnswer, seen: list[str], corpus: Corpus,
                       messages: list | None = None, live_agent=None, live_response=None) -> tuple[list[Grade],dict]:
    allowed = corpus.allowed_ids(case["allowed_document_ids"])
    citation_docs = {corpus.passages[p]["document_id"] for p in answer.citations if p in corpus.passages}
    is_answer = answer.disposition == "answer"
    has_factual_task = case["expected_disposition"] == "answer"
    scope_applies = is_answer and has_factual_task

    @evaluator
    def task_intent(response: str):
        response = answer.text
        matches = all(re.search(pattern,response,re.I) for pattern in case["concepts"])
        expected_count = "twelve|12" if case["id"] == "proposed-1789" else "ten|10" if case["id"] in {"ratified-1791","clear-context"} else None
        if expected_count and re.search(r"\b(?:not|rather than|instead of)\s+(?:"+expected_count+r")\b",response,re.I):
            matches = False
        return CheckResult(bool(matches),
            "The response includes the declared concepts for this task. " + CRITERIA_NOTE if matches
            else "A required concept is missing or addresses a different event or question.", "task_intent")

    @evaluator
    def citation_provenance(response: str):
        valid = all(p in corpus.passages and p in seen for p in answer.citations)
        if is_answer and has_factual_task:
            valid = valid and bool(answer.citations)
        return CheckResult(bool(valid), "Citations point to passages returned by the tools."
            if valid else "A factual answer lacks a citation, or cites a passage the agent did not retrieve.", "citation_provenance")

    @evaluator
    def evidence_boundary(response: str):
        ids = set(seen) | set(answer.citations)
        valid = all(p in corpus.passages and corpus.passages[p]["document_id"] in allowed for p in ids)
        return CheckResult(bool(valid), "All observed and cited passages are inside this case's authorized evidence."
            if valid else "The response or trace uses a document outside this case's evidence boundary.", "evidence_boundary")

    @evaluator
    def scope_alignment(response: str):
        documents = not case["required_document_ids"] or bool(set(case["required_document_ids"]) & citation_docs)
        passages = not case["reference_passage_ids"] or bool(set(case["reference_passage_ids"]) & set(answer.citations))
        date_ok = not case.get("as_of") or answer.as_of == case["as_of"]
        valid = not scope_applies or (documents and passages and date_ok)
        return CheckResult(bool(valid), "An approved task-relevant passage, document, and declared date match the task."
            if scope_applies and valid else "No factual scope assertion is required for this response."
            if not scope_applies else "The cited clause, authority, or declared time period does not match the question.", "scope_alignment")

    @evaluator
    def appropriate_response(response: str):
        valid = answer.disposition == case["expected_disposition"]
        return CheckResult(valid, "The agent chose the required response behavior."
            if valid else f"The case calls for {case['expected_disposition']}, but the agent chose {answer.disposition}.",
            "appropriate_response")

    @evaluator
    def source_value_match(response: str):
        response = answer.text
        # Deliberately weak: some salient words appearing in an authentic source
        # do not establish that the source supports this complete claim.
        texts = []
        for pid in answer.citations:
            if pid in corpus.passages:
                d = corpus.documents[corpus.passages[pid]["document_id"]]
                texts.append(corpus.passages[pid]["text"]+" "+" ".join(d.get("annotations",[])))
        words = {w.lower() for w in re.findall(r"\b[a-zA-Z]{4,}\b|\b\d+\b",response)}
        source = " ".join(texts).lower()
        valid = bool(texts) and any(w in source for w in words)
        return CheckResult(valid, "Some answer words appear in a cited authentic source. This does not check intent, authority, dates, or entailment."
            if valid else "This simple checker could not match an answer to a cited source.", "source_value_match")

    conversation = messages or [Message("user",[case["question"]]),Message("assistant",[answer.text])]
    # Direct EvalItem supports fixtures and full captured conversation without rerunning the agent.
    item = EvalItem(conversation=conversation, context=case["expected_behavior"])
    strong_evaluator = LocalEvaluator(task_intent,citation_provenance,evidence_boundary,scope_alignment,appropriate_response)
    weak_evaluator = LocalEvaluator(source_value_match)
    if live_agent is not None and live_response is not None:
        from agent_framework import evaluate_agent
        strong = (await evaluate_agent(agent=live_agent, queries=case["question"], responses=live_response, evaluators=strong_evaluator))[0]
        weak = (await evaluate_agent(agent=live_agent, queries=case["question"], responses=live_response, evaluators=weak_evaluator))[0]
    else:
        strong = await strong_evaluator.evaluate([item],eval_name="Task-aware local checks")
        weak = await weak_evaluator.evaluate([item],eval_name="Weak checker demonstration")
    grades = []
    for sdk,kind in [(strong,"deterministic"),(weak,"weak_checker")]:
        for score in sdk.items[0].scores:
            not_applicable = score.name == "scope_alignment" and not scope_applies
            if score.name == "citation_provenance" and not is_answer and not answer.citations:
                not_applicable = True
            grades.append(Grade(name=score.name,label=LABELS[score.name],kind=kind,
                status="not_applicable" if not_applicable else "pass" if score.passed else "fail",
                required=kind!="weak_checker" and not not_applicable,
                reason=score.sample.get("reason",""), score=None if not_applicable else score.score,
                evidence_ids=answer.citations))
    grades.append(Grade(name="semantic_judge",label="Optional AI judge",kind="ai_judge",status="not_assessed",
        required=False,reason="No AI judge was run. Local checks do not establish every aspect of meaning."))
    def serialize(sdk):
        return {"provider":sdk.provider,"status":sdk.status,"result_counts":sdk.result_counts,
            "per_evaluator":sdk.per_evaluator,"items":[dataclasses.asdict(i) for i in sdk.items]}
    return grades, {"sdk":"Microsoft Agent Framework","version":"1.24.0",
        "evaluation_type":"evaluate_agent(responses=...)" if live_response is not None else "LocalEvaluator.evaluate(EvalItem)","strong":serialize(strong),"weak":serialize(weak)}

