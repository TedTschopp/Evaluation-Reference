"""Public, versioned contracts shared by the API and both teaching apps."""
from __future__ import annotations
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator

class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

class Authentication(StrictModel):
    type: Literal["none", "bearer"] = "none"
    environment_variable: str | None = Field(default=None, pattern=r"^[A-Z][A-Z0-9_]{0,63}$")

class GenerationOptions(StrictModel):
    json_schema: bool = False
    temperature: float | None = Field(default=0, ge=0, le=2)
    max_output_tokens: int = Field(default=1200, ge=64, le=4096)
    timeout_seconds: int = Field(default=60, ge=5, le=120)

class Capabilities(StrictModel):
    tools: bool | None = None
    streaming: bool | None = None

class ModelEndpointDefinition(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    id: str = Field(default="my-endpoint", pattern=r"^[a-zA-Z0-9_-]{1,64}$")
    name: str = Field(default="My model", min_length=1, max_length=100)
    protocol: str = Field(default="openai_chat_completions", pattern=r"^[a-z][a-z0-9_]{0,63}$")
    base_url: str = Field(min_length=8, max_length=2048)
    model: str = Field(min_length=1, max_length=200)
    authentication: Authentication = Field(default_factory=Authentication)
    generation: GenerationOptions = Field(default_factory=GenerationOptions)
    capabilities: Capabilities = Field(default_factory=Capabilities)

class EndpointConnection(StrictModel):
    definition: ModelEndpointDefinition
    api_key: SecretStr | None = Field(default=None, exclude=True)

class ReleasePolicy(StrictModel):
    id: str = "teaching-default-v1"
    minimum_pass_rate: float = Field(default=.9, ge=0, le=1)
    maximum_critical_failures: int = Field(default=0, ge=0, le=12)
    require_complete: bool = True

class RunRequest(StrictModel):
    case_ids: list[str] = Field(min_length=1, max_length=12)
    profile: Literal["baseline", "candidate", "revised"] = "revised"
    agent: EndpointConnection
    judge: EndpointConnection | None = None
    repetitions: int = Field(default=1, ge=1, le=3)
    policy: ReleasePolicy = Field(default_factory=ReleasePolicy)

    @field_validator("case_ids")
    @classmethod
    def unique_cases(cls, value: list[str]) -> list[str]:
        if len(set(value)) != len(value):
            raise ValueError("Each case must be selected only once.")
        return value

class Grade(StrictModel):
    name: str
    label: str
    kind: Literal["deterministic", "ai_judge", "weak_checker", "reference"]
    status: Literal["pass", "fail", "error", "not_assessed", "not_applicable"]
    required: bool = True
    reason: str
    score: float | None = None
    evidence_ids: list[str] = Field(default_factory=list)

class AgentAnswer(StrictModel):
    text: str = Field(max_length=30000)
    citations: list[str] = Field(default_factory=list, max_length=30)
    disposition: Literal["answer", "clarify", "insufficient_evidence"] = "answer"
    as_of: str | None = None

class CaseResult(StrictModel):
    case_id: str
    repetition: int = 1
    profile: str
    source_kind: Literal["authored_fixture", "captured_model_run"]
    answer: AgentAnswer
    events: list[dict[str, Any]] = Field(default_factory=list)
    messages: list[dict[str, Any]] = Field(default_factory=list)
    grades: list[Grade] = Field(default_factory=list)
    status: Literal["pass", "fail", "error", "unresolved"]
    critical: bool
    latency_ms: float | None = None
    tokens: dict[str, int] | None = None
    framework: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None

class ReleaseDecision(StrictModel):
    verdict: Literal["hold", "eligible"]
    passed: int
    total: int
    pass_rate: float
    critical_failures: int
    unresolved: int
    reasons: list[str]
    policy: ReleasePolicy

class RunBundle(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    id: str
    created_at: str
    mode: Literal["replay", "live"]
    provenance: str
    versions: dict[str, str]
    endpoint: ModelEndpointDefinition | None = None
    judge_endpoint: ModelEndpointDefinition | None = None
    expected_results: int = Field(ge=0)
    judge_calibration: list[dict[str, Any]] = Field(default_factory=list)
    results: list[CaseResult]
    decision: ReleaseDecision

def decide_release(results: list[CaseResult], policy: ReleasePolicy, expected_total: int | None = None) -> ReleaseDecision:
    """Release is explicit policy over cases, independent of average scores."""
    total = max(len(results), expected_total or 0)
    def failed(r):
        return r.status == "fail" or any(g.required and g.status == "fail" for g in r.grades)
    def incomplete(r):
        return r.status in {"error", "unresolved"} or any(g.required and g.status in {"error", "not_assessed"} for g in r.grades)
    passed = sum(r.status == "pass" and not failed(r) and not incomplete(r) for r in results)
    critical = sum(r.critical and failed(r) for r in results)
    unresolved = sum(incomplete(r) for r in results) + total - len(results)
    rate = passed / total if total else 0
    reasons: list[str] = []
    if not total:
        reasons.append("No cases have been evaluated.")
    if critical > policy.maximum_critical_failures:
        reasons.append(f"{critical} critical case(s) failed; policy allows {policy.maximum_critical_failures}.")
    if policy.require_complete and unresolved:
        reasons.append(f"{unresolved} case(s) have required evaluations unresolved or errored.")
    if rate < policy.minimum_pass_rate:
        reasons.append(f"{passed}/{total} cases passed; the required rate is {policy.minimum_pass_rate:.0%}.")
    return ReleaseDecision(verdict="hold" if reasons else "eligible", passed=passed, total=total,
        pass_rate=rate, critical_failures=critical, unresolved=unresolved,
        reasons=reasons or ["The tested cases meet this policy. This is bounded evidence, not a guarantee."], policy=policy)

