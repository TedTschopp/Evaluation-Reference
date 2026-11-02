"""Validate imported evidence for consistency; this does not authenticate a run."""
from .corpus import case_by_id
from .grading import result_status
from .models import RunBundle,decide_release

CANONICAL_CHECKS={"task_intent","citation_provenance","evidence_boundary","scope_alignment","appropriate_response"}

def validate_imported_bundle(value) -> RunBundle:
    bundle=RunBundle.model_validate_json(value) if isinstance(value,(str,bytes)) else RunBundle.model_validate(value)
    if bundle.expected_results not in {12,36} or len(bundle.results)>bundle.expected_results:
        raise ValueError("The release denominator must cover the complete twelve-case suite.")
    repetitions=bundle.expected_results//12
    identities=set()
    for result in bundle.results:
        case=case_by_id(result.case_id)
        identity=(result.case_id,result.repetition)
        if identity in identities or not 1<=result.repetition<=repetitions:
            raise ValueError("Duplicate or invalid case/repetition identity.")
        identities.add(identity)
        if result.critical!=case["critical"]:
            raise ValueError("Critical-case metadata does not match the case manifest.")
        if result.status=="error":
            if not result.error:
                raise ValueError("Execution errors need an explanation.")
            continue
        grades={g.name:g for g in result.grades}
        if len(grades)!=len(result.grades) or not CANONICAL_CHECKS<=grades.keys():
            raise ValueError("The required canonical criteria are missing or duplicated.")
        factual=result.answer.disposition=="answer"
        applicable=factual and case["expected_disposition"]=="answer"
        for name in CANONICAL_CHECKS:
            grade=grades[name]
            na=(name=="scope_alignment" and not applicable) or (name=="citation_provenance" and not factual and not result.answer.citations)
            if grade.kind!="deterministic" or grade.required==na or (grade.status=="not_applicable")!=na:
                raise ValueError("Criterion applicability or required status was altered.")
        judge=grades.get("semantic_judge")
        if bundle.judge_endpoint and (not judge or not judge.required):
            raise ValueError("A configured AI judge is a required assessment.")
        if result.status!=result_status(result.grades):
            raise ValueError("The result status contradicts its required evaluations.")
    bundle.decision=decide_release(bundle.results,bundle.decision.policy,bundle.expected_results)
    return bundle

