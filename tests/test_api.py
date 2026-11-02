import asyncio
import json
from fastapi.testclient import TestClient
from eval_lab import api
from eval_lab.models import ModelEndpointDefinition

def connection():
    return {"definition":ModelEndpointDefinition(base_url="http://127.0.0.1:11435",model="test").model_dump(),"api_key":"do-not-echo-this"}

def test_health_has_no_secrets():
    with TestClient(api.app) as client:
        r=client.get("/api/health")
        assert r.status_code==200 and r.json()["framework"]=="agent-framework-core==1.24.0"
        assert r.headers["cache-control"]=="no-store"

def test_validation_never_echoes_credentials():
    with TestClient(api.app) as client:
        r=client.post("/api/connections/test",json={"definition":{"model":[]},"api_key":"do-not-echo-this"})
        assert r.status_code==422 and "do-not-echo-this" not in r.text

def test_connection_operation(monkeypatch):
    async def probe(*args):return {"connected":True,"tools":True,"message":"Verified"}
    monkeypatch.setattr(api,"test_connection",probe)
    with TestClient(api.app) as client:
        r=client.post("/api/connections/test",json=connection())
        assert r.status_code==200 and r.json()["tools"]

def test_origin_and_payload_limits():
    with TestClient(api.app) as client:
        assert client.post("/api/connections/test",json=connection(),headers={"Origin":"https://untrusted.example"}).status_code==403
        assert client.post("/api/connections/test",content=b"x"*65537).status_code==413

def test_runs_stream_terminal_result(monkeypatch):
    async def execute(request,hosted,emit):
        emit({"type":"started","expected_results":1})
        emit({"type":"complete","data":{"test":"terminal-result"}})
    monkeypatch.setattr(api,"execute_run",execute)
    with TestClient(api.app) as client:
        r=client.post("/api/runs",json={"case_ids":["senate-1789"],"agent":connection()})
        events=[json.loads(line) for line in r.text.splitlines()]
        assert r.status_code==200 and [e["type"] for e in events]==["started","complete"]
        assert api.slots._value==2

def test_unknown_case_and_hosted_private_endpoint(monkeypatch):
    with TestClient(api.app) as client:
        assert client.post("/api/runs",json={"case_ids":["unknown"],"agent":connection()}).status_code==400
        monkeypatch.setattr(api,"HOSTED",True)
        assert client.post("/api/connections/test",json=connection()).status_code==400

