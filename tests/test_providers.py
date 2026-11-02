import asyncio
import json
import httpx
import pytest
from eval_lab.models import EndpointConnection,ModelEndpointDefinition
from eval_lab import providers

def definition(protocol="openai_chat_completions",auth="none"):
    return EndpointConnection(definition=ModelEndpointDefinition(protocol=protocol,
        base_url="https://models.example/v1" if protocol=="openai_chat_completions" else "https://models.example",
        model="test-model",authentication={"type":auth}),api_key="sensitive-test-key" if auth=="bearer" else None)

@pytest.mark.asyncio
@pytest.mark.parametrize("protocol",["openai_chat_completions","ollama"])
async def test_real_sdk_function_round_trip(monkeypatch,protocol):
    requests=[]
    def handle(request):
        body=json.loads(request.content);requests.append((request,body))
        assert "authorization" not in request.headers
        done=any(m["role"]=="tool" for m in body["messages"])
        if protocol=="openai_chat_completions":
            message={"role":"assistant","content":"connected" if done else None}
            if not done:message["tool_calls"]=[{"id":"probe-1","type":"function","function":{"name":"endpoint_probe","arguments":'{"value":"evaluation-lab"}'}}]
            return httpx.Response(200,json={"id":"test","object":"chat.completion","created":0,"model":"test-model",
                "choices":[{"index":0,"message":message,"finish_reason":"stop" if done else "tool_calls"}]})
        message={"role":"assistant","content":"connected" if done else ""}
        if not done:message["tool_calls"]=[{"function":{"name":"endpoint_probe","arguments":{"value":"evaluation-lab"}}}]
        return httpx.Response(200,json={"model":"test-model","created_at":"2026-11-02T00:00:00Z","message":message,"done":True})
    monkeypatch.setattr(providers,"transport",lambda hosted:httpx.MockTransport(handle))
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT","https://unrelated-azure.example")
    result=await providers.test_connection(definition(protocol),True)
    assert result["tools"] is True and len(requests)==2
    assert all(request.url.host=="models.example" for request,_ in requests)

@pytest.mark.asyncio
async def test_invalid_credentials_are_redacted(monkeypatch):
    def handle(request):
        return httpx.Response(401,json={"error":{"message":"sensitive-test-key","type":"authentication_error"}})
    monkeypatch.setattr(providers,"transport",lambda hosted:httpx.MockTransport(handle))
    with pytest.raises(Exception) as caught:
        await providers.test_connection(definition(auth="bearer"),True)
    message=providers.safe_error(caught.value)
    assert "sensitive-test-key" not in message and "authentication" in message

@pytest.mark.asyncio
async def test_redirect_not_followed(monkeypatch):
    requests=[]
    def handle(request):
        requests.append(str(request.url))
        return httpx.Response(307,headers={"Location":"http://169.254.169.254/latest"})
    monkeypatch.setattr(providers,"transport",lambda hosted:httpx.MockTransport(handle))
    with pytest.raises(Exception):
        await providers.test_connection(definition(),True)
    assert len(requests)==1

@pytest.mark.asyncio
async def test_cancellation_releases_provider(monkeypatch):
    started=asyncio.Event();cancelled=asyncio.Event()
    async def handle(request):
        started.set()
        try:
            await asyncio.sleep(30)
        except asyncio.CancelledError:
            cancelled.set();raise
    monkeypatch.setattr(providers,"transport",lambda hosted:httpx.MockTransport(handle))
    task=asyncio.create_task(providers.test_connection(definition(),True))
    await started.wait();task.cancel()
    with pytest.raises(asyncio.CancelledError):await task
    assert cancelled.is_set()

def test_credentials_not_exported():
    c=definition(auth="bearer")
    assert "sensitive-test-key" not in c.model_dump_json()
    assert "api_key" not in c.model_dump()

