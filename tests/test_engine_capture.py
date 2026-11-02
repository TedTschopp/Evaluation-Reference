import json
from contextlib import asynccontextmanager
import pytest
from agent_framework import Agent,BaseChatClient,ChatMiddlewareLayer,ChatResponse,Content,FunctionInvocationLayer,Message
from agent_framework.observability import ChatTelemetryLayer
from eval_lab import engine
from eval_lab.corpus import Corpus,case_by_id
from eval_lab.models import EndpointConnection,ModelEndpointDefinition

class ScriptedClient(FunctionInvocationLayer,ChatMiddlewareLayer,ChatTelemetryLayer,BaseChatClient):
    def __init__(self,responses):
        super().__init__(middleware=[]);self.responses=iter(responses)
    def _inner_get_response(self,*,messages,stream,options,**kwargs):
        async def respond():
            await self._validate_options(options)
            return next(self.responses)
        return respond()

@pytest.mark.asyncio
@pytest.mark.parametrize("valid",[True,False])
async def test_actual_sdk_capture_retains_failure_trace_and_redacts_reflections(monkeypatch,valid):
    secret="sensitive-private-test-key"
    case=case_by_id("senate-1789")
    output=json.dumps({"text":"State legislatures chose senators. "+secret,"citations":["constitution.article-1.section-3.p1"],
        "disposition":"answer","as_of":case["as_of"]}) if valid else "An invalid output containing "+secret
    client=ScriptedClient([
        ChatResponse(messages=Message("assistant",[Content.from_function_call(call_id="one",name="retrieve_passage",arguments={"passage_id":"constitution.article-1.section-3.p1"})])),
        ChatResponse(messages=Message("assistant",[output])),
    ])
    @asynccontextmanager
    async def factory(*args):
        yield client
    monkeypatch.setattr(engine,"model_client",factory)
    connection=EndpointConnection(definition=ModelEndpointDefinition(base_url="https://models.example/v1",model="test",authentication={"type":"bearer"}),api_key=secret)
    events=[]
    result=await engine.run_case(case,"revised",connection,Corpus(),True,1,events.append)
    assert any(e["type"]=="tool_result" for e in result.events)
    assert result.messages
    assert secret not in result.model_dump_json()
    assert secret not in json.dumps(events)
    if valid:
        assert result.framework["evaluation_type"]=="evaluate_agent(responses=...)"
        assert result.status=="pass"
    else:
        assert result.status=="error" and result.error

