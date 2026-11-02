"""Rebuild teaching results with the actual pinned Microsoft local evaluators."""
from __future__ import annotations
import asyncio
import json
from datetime import datetime,timezone
from pathlib import Path
from agent_framework import Message, Content
from .corpus import Corpus,DATA_DIR,case_by_id,load_json
from .engine import versions
from .grading import grade_answer,result_status
from .models import AgentAnswer,CaseResult,ReleasePolicy,RunBundle,decide_release

async def fixture_result(seed: dict,profile: str,corpus: Corpus) -> CaseResult:
    case = case_by_id(seed["case_id"])
    answer = AgentAnswer.model_validate({k:seed[k] for k in ("text","citations","disposition","as_of")})
    seen = seed["retrieved_passage_ids"]
    passages = [corpus.retrieve(pid,["*"]) for pid in seen]
    events = []
    messages = [Message("user",[case["question"]])]
    for i,passage in enumerate(passages):
        call_id = f"fixture-{i+1}"
        events.extend([
            {"type":"tool_call","sequence":len(events)+1,"name":"retrieve_passage","arguments":{"passage_id":passage["id"]}},
            {"type":"tool_result","sequence":len(events)+2,"name":"retrieve_passage","passage_ids":[passage["id"]]},
        ])
        messages.extend([
            Message("assistant",[Content.from_function_call(call_id=call_id,name="retrieve_passage",arguments={"passage_id":passage["id"]})]),
            Message("tool",[Content.from_function_result(call_id=call_id,result=json.dumps(passage,ensure_ascii=False))]),
        ])
    messages.append(Message("assistant",[answer.text]))
    events.append({"type":"answer","sequence":len(events)+1,"text":answer.text,"citations":answer.citations})
    grades,framework = await grade_answer(case,answer,seen,corpus,messages=messages)
    return CaseResult(case_id=case["id"],profile=profile,source_kind="authored_fixture",answer=answer,
        events=events,messages=[m.to_dict() for m in messages],grades=grades,
        status=result_status(grades),critical=case["critical"],framework=framework)

async def generate_replays(write: bool=True) -> dict:
    corpus = Corpus()
    seeds = load_json("fixture-seeds.json")
    profiles = []
    for profile in seeds["profiles"]:
        results = [await fixture_result(seed,profile["id"],corpus) for seed in profile["answers"]]
        bundle = RunBundle(id="teaching-"+profile["id"]+"-v1",created_at="2026-11-02T00:00:00+00:00",
            mode="replay",provenance=seeds["provenance"],versions=versions(corpus),
            expected_results=len(results),results=results,decision=decide_release(results,ReleasePolicy()))
        profiles.append({"id":profile["id"],"title":profile["title"],"description":profile["description"],
            "bundle":bundle.model_dump(mode="json")})
    calibration = []
    for seed in seeds["calibration"]:
        result = await fixture_result(seed,"calibration",corpus)
        weak = next(g for g in result.grades if g.kind=="weak_checker")
        calibration.append({**seed,"actual_pass":result.status=="pass",
            "weak_pass":weak.status=="pass","matches_reference":(result.status=="pass")==seed["expected_pass"],
            "result":result.model_dump(mode="json")})
    result = {"schema_version":"1.0","generated_at":datetime.now(timezone.utc).isoformat(),
        "provenance":seeds["provenance"],"profiles":profiles,"calibration":calibration}
    if write:
        (DATA_DIR/"replays.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return result

if __name__=="__main__":
    value=asyncio.run(generate_replays())
    for profile in value["profiles"]:
        d=profile["bundle"]["decision"]
        print(f"{profile['id']}: {d['passed']}/{d['total']} {d['verdict']}")
    print("Calibration:",sum(x["matches_reference"] for x in value["calibration"]),"/",len(value["calibration"]))

