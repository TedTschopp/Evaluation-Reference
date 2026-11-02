import copy
import json
import pytest
from eval_lab.corpus import load_json
from eval_lab.models import Grade,ReleasePolicy,CaseResult,decide_release
from eval_lab.grading import result_status
from eval_lab.validation import validate_imported_bundle

def revised():
    return copy.deepcopy(load_json("replays.json")["profiles"][2]["bundle"])

def test_import_recalculates_counts():
    value=revised();value["decision"]["passed"]=0
    assert validate_imported_bundle(value).decision.passed==12

@pytest.mark.parametrize("tamper",["duplicate","critical","invented","applicability","summary"])
def test_reject_inconsistent_imports(tamper):
    value=revised()
    if tamper=="duplicate":value["results"]=[copy.deepcopy(value["results"][0]) for _ in range(12)]
    if tamper=="critical":value["results"][1]["critical"]=not value["results"][1]["critical"]
    if tamper=="invented":value["results"][0]["grades"]=[{"name":"anything","label":"anything","kind":"deterministic","status":"pass","required":True,"reason":"asserted"}]
    if tamper=="applicability":value["results"][0]["grades"][0]["required"]=False
    if tamper=="summary":value["results"][0]["status"]="fail"
    with pytest.raises(ValueError):validate_imported_bundle(value)

def test_judge_error_cannot_hide_critical_failure():
    value=copy.deepcopy(load_json("replays.json")["profiles"][1]["bundle"])
    results=[CaseResult.model_validate(r) for r in value["results"]]
    critical=next(r for r in results if r.critical)
    critical.grades.append(Grade(name="judge",label="Judge",kind="ai_judge",status="error",required=True,reason="Unavailable"))
    critical.status=result_status(critical.grades)
    assert critical.status=="fail"
    decision=decide_release(results,ReleasePolicy(require_complete=False))
    assert decision.verdict=="hold" and decision.critical_failures==1 and decision.unresolved==1

