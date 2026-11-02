import asyncio
import json
import socket
import httpx
import pytest
import uvicorn
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

@pytest.mark.asyncio
async def test_real_http_disconnect_cancels_work_and_releases_bounded_slots(monkeypatch):
    cancelled=[]
    async def slow_run(request,hosted,emit):
        emit({"type":"started"})
        try:
            await asyncio.sleep(30)
        finally:
            cancelled.append(True)
    monkeypatch.setattr(api,"execute_run",slow_run)
    sock=socket.socket();sock.bind(("127.0.0.1",0))
    port=sock.getsockname()[1]
    server=uvicorn.Server(uvicorn.Config(api.app,log_level="error",lifespan="off"))
    serving=asyncio.create_task(server.serve(sockets=[sock]))
    try:
        async with asyncio.timeout(5):
            while not server.started:await asyncio.sleep(.01)
        async with httpx.AsyncClient(base_url=f"http://127.0.0.1:{port}",timeout=5) as client:
            payload={"case_ids":["senate-1789"],"agent":connection()}
            async with client.stream("POST","/api/runs",json=payload) as first:
                first_lines=first.aiter_lines()
                assert json.loads(await anext(first_lines))["type"]=="started"
                async with client.stream("POST","/api/runs",json=payload) as second:
                    second_lines=second.aiter_lines()
                    assert json.loads(await anext(second_lines))["type"]=="started"
                    assert (await client.post("/api/runs",json=payload)).status_code==429
                    assert (await client.get("/api/health")).json()["active_runs"]==2
            for _ in range(100):
                if api.slots._value==2 and len(cancelled)==2:break
                await asyncio.sleep(.05)
            assert (api.slots._value,len(cancelled))==(2,2)
            assert (await client.get("/api/health")).json()["active_runs"]==0
    finally:
        server.should_exit=True
        await serving

