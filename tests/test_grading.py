import asyncio
import pytest
from eval_lab.corpus import Corpus,case_by_id,load_json
from eval_lab.engine import parse_answer
from eval_lab.grading import grade_answer,result_status
from eval_lab.models import AgentAnswer,ReleasePolicy,decide_release
from eval_lab.replay import generate_replays

@pytest.fixture(scope="module")
def replays():
    return asyncio.run(generate_replays(write=False))

def test_real_framework_matrix(replays):
    expected={"baseline":(8,"hold"),"candidate":(11,"hold"),"revised":(12,"eligible")}
    for profile in replays["profiles"]:
        bundle=profile["bundle"]
        assert (bundle["decision"]["passed"],bundle["decision"]["verdict"])==expected[profile["id"]]
        assert all(r["framework"]["strong"]["provider"]=="Local" for r in bundle["results"])

def test_real_grader_calibration(replays):
    assert len(replays["calibration"])==8
    assert all(r["matches_reference"] for r in replays["calibration"])
    misleading=next(r for r in replays["calibration"] if r["id"]=="wrong-12-ratified")
    assert misleading["weak_pass"] is True and misleading["actual_pass"] is False

@pytest.mark.asyncio
async def test_valid_paraphrase_and_unretrieved_citation():
    corpus=Corpus();case=case_by_id("senate-1789")
    answer=AgentAnswer(text="State legislatures selected their senators.",citations=["constitution.article-1.section-3.p1"],
        disposition="answer",as_of=case["as_of"])
    grades,_=await grade_answer(case,answer,answer.citations,corpus)
    assert result_status(grades)=="pass"
    grades,_=await grade_answer(case,answer,[],corpus)
    assert result_status(grades)=="fail"
    assert next(g for g in grades if g.name=="citation_provenance").status=="fail"

@pytest.mark.asyncio
async def test_correct_guess_cannot_escape_boundary():
    corpus=Corpus();case=case_by_id("evidence-restricted")
    answer=AgentAnswer(text="State legislatures selected senators.",citations=["constitution.article-1.section-3.p1"],
        disposition="answer",as_of=case["as_of"])
    grades,_=await grade_answer(case,answer,[],corpus)
    assert next(g for g in grades if g.name=="evidence_boundary").status=="fail"
    with pytest.raises(ValueError):
        corpus.retrieve(answer.citations[0],case["allowed_document_ids"])
    assert all(p["document_id"]=="declaration" for p in corpus.search("senators legislature",case["allowed_document_ids"]))

def test_partial_suite_cannot_pass_release(replays):
    from eval_lab.models import CaseResult
    one=CaseResult.model_validate(replays["profiles"][2]["bundle"]["results"][0])
    d=decide_release([one],ReleasePolicy(),expected_total=12)
    assert d.verdict=="hold" and d.unresolved==11 and d.total==12

def test_format_errors_are_not_answers():
    with pytest.raises(ValueError,match="JSON contract"):
        parse_answer("The answer is ten.")
    assert parse_answer('{"text":"Ten.","citations":[],"disposition":"answer","as_of":null}').text=="Ten."

@pytest.mark.asyncio
async def test_expected_word_inside_negation_is_not_success():
    case=case_by_id("ratified-1791");corpus=Corpus()
    ids=["amendment-01.p1","amendment-10.p1"]
    answer=AgentAnswer(text="Twelve amendments were ratified in 1791, not ten.",citations=ids,as_of=case["as_of"])
    grades,_=await grade_answer(case,answer,ids,corpus)
    assert next(g for g in grades if g.name=="task_intent").status=="fail"

@pytest.mark.asyncio
async def test_wrong_clause_in_right_document_is_not_support():
    case=case_by_id("senate-1789");corpus=Corpus();ids=["constitution.article-2.section-1.p2"]
    answer=AgentAnswer(text="The legislature directs the choice of electors.",citations=ids,as_of=case["as_of"])
    grades,_=await grade_answer(case,answer,ids,corpus)
    assert next(g for g in grades if g.name=="scope_alignment").status=="fail"

def test_errors_and_missing_assessments_block_release(replays):
    from eval_lab.models import CaseResult,Grade
    r=CaseResult.model_validate(replays["profiles"][2]["bundle"]["results"][0])
    r.grades.append(Grade(name="judge",label="Judge",kind="ai_judge",status="error",required=True,reason="Unavailable"))
    r.status=result_status(r.grades)
    assert r.status=="unresolved"
    assert decide_release([r],ReleasePolicy()).verdict=="hold"

