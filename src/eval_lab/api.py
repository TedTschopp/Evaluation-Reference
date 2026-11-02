"""Three API operations; keys and conversations are never stored."""
from __future__ import annotations
import asyncio
import json
import os
import time
import anyio
from collections import defaultdict,deque
from pathlib import Path
from fastapi import FastAPI,HTTPException,Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse,StreamingResponse
from fastapi.staticfiles import StaticFiles
from . import __version__
from .corpus import case_by_id
from .engine import execute_run
from .models import EndpointConnection,RunRequest
from .network import validate_endpoint_url
from .providers import ADAPTERS,safe_error,test_connection

HOSTED = os.environ.get("EVAL_LAB_HOSTED","0")=="1"
app = FastAPI(title="Founding Documents AI Evaluation Lab",version=__version__)
slots = asyncio.Semaphore(2)
limits: dict[str,deque] = defaultdict(deque)

@app.middleware("http")
async def controls(request: Request, call_next):
    if request.url.path.startswith("/api/"):
        length = request.headers.get("content-length")
        if length and (not length.isdigit() or int(length)>65536):
            return JSONResponse({"detail":"Request exceeds the 64 KiB limit."},status_code=413)
        if request.method=="POST":
            origin = request.headers.get("origin")
            allowed = {f"{request.url.scheme}://{request.url.netloc}"}
            allowed |= {value.strip() for value in os.environ.get("EVAL_LAB_ALLOWED_ORIGINS", "").split(",") if value.strip()}
            if not HOSTED:
                allowed |= {"http://127.0.0.1:5173","http://localhost:5173","http://127.0.0.1:5174","http://localhost:5174","http://localhost:8000","http://127.0.0.1:8000"}
            if origin and origin not in allowed:
                return JSONResponse({"detail":"This origin is not permitted."},status_code=403)
            # Bound chunked requests too, before FastAPI/Pydantic parse them.
            body = bytearray()
            async for chunk in request.stream():
                body.extend(chunk)
                if len(body)>65536:
                    return JSONResponse({"detail":"Request exceeds the 64 KiB limit."},status_code=413)
            request._body = bytes(body)
            if HOSTED:
                now=time.monotonic()
                trusted_header=os.environ.get("EVAL_LAB_CLIENT_IP_HEADER", "")
                address=(request.headers.get(trusted_header) if trusted_header else None) or (request.client.host if request.client else "unknown")
                entries=limits[address]
                while entries and now-entries[0]>60:
                    entries.popleft()
                if len(entries)>=10:
                    return JSONResponse({"detail":"The demo permits ten live requests per minute. Try again shortly."},status_code=429)
                entries.append(now)
                if len(limits)>2000:
                    for key in list(limits):
                        if not limits[key] or now-limits[key][-1]>60:
                            limits.pop(key,None)
        response=await call_next(request)
        response.headers["Cache-Control"]="no-store"
        response.headers["X-Content-Type-Options"]="nosniff"
        return response
    return await call_next(request)

@app.exception_handler(RequestValidationError)
async def validation_error(request,error):
    # Pydantic error payloads may echo rejected input, including a credential.
    fields=[".".join(str(x) for x in item["loc"]) for item in error.errors()]
    return JSONResponse({"detail":"The request does not match the published contract.","fields":fields},status_code=422)

@app.get("/api/health")
async def health():
    return {"status":"ok","version":__version__,"framework":"agent-framework-core==1.24.0",
        "hosted":HOSTED,"protocols":list(ADAPTERS),"storage":"none","concurrent_runs":2,"active_runs":2-slots._value}

def validate_connection(connection):
    try:
        validate_endpoint_url(connection.definition.base_url,HOSTED)
        if connection.definition.protocol not in ADAPTERS:
            raise ValueError("This endpoint protocol has no installed adapter.")
    except ValueError as error:
        raise HTTPException(status_code=400,detail=safe_error(error)) from error

@app.post("/api/connections/test")
async def connection_test(connection: EndpointConnection):
    validate_connection(connection)
    if slots.locked():
        raise HTTPException(429,"Both live evaluation slots are busy. Try again shortly.")
    async with slots:
        try:
            async with asyncio.timeout(125):
                return await test_connection(connection,HOSTED)
        except Exception as error:
            return JSONResponse({"connected":False,"tools":False,"message":safe_error(error)},status_code=400)

@app.post("/api/runs")
async def run(request: RunRequest, http_request: Request):
    validate_connection(request.agent)
    if request.judge:
        validate_connection(request.judge)
    try:
        for case_id in request.case_ids:
            case_by_id(case_id)
    except ValueError as error:
        raise HTTPException(400,str(error)) from error
    if slots.locked():
        raise HTTPException(429,"Both live evaluation slots are busy. Try again shortly.")
    await slots.acquire()
    async def stream():
        queue=asyncio.Queue(maxsize=1000)
        def emit(event):
            queue.put_nowait(event)
        async def perform():
            try:
                async with asyncio.timeout(300):
                    await execute_run(request,HOSTED,emit)
            except asyncio.CancelledError:
                raise
            except Exception as error:
                emit({"type":"error","message":safe_error(error)})
        task=asyncio.create_task(perform())
        async def watch_disconnect():
            # ASGI 2.4 detects disconnects on the next send. Explicitly watch
            # while a provider is busy so Stop need not wait for a heartbeat.
            while not await http_request.is_disconnected():
                await asyncio.sleep(.1)
            task.cancel()
            await queue.put(None)
        disconnected=asyncio.create_task(watch_disconnect())
        try:
            while not task.done() or not queue.empty():
                try:
                    item=await asyncio.wait_for(queue.get(),timeout=10)
                    if item is None:
                        break
                    yield json.dumps(item,ensure_ascii=False)+"\n"
                except TimeoutError:
                    yield '{"type":"heartbeat"}\n'
            await task
        finally:
            disconnected.cancel()
            if not task.done():
                task.cancel()
            # Starlette closes disconnected streams inside an AnyIO cancel
            # scope. Shield cleanup so cancellation cannot skip slot release.
            with anyio.CancelScope(shield=True):
                try:
                    await asyncio.gather(task,disconnected,return_exceptions=True)
                finally:
                    slots.release()
    return StreamingResponse(stream(),media_type="application/x-ndjson",
        headers={"Cache-Control":"no-store","X-Accel-Buffering":"no"})

default_static=Path.cwd()/"web"/"dist"
if not default_static.is_dir():
    default_static=Path(__file__).resolve().parents[2]/"web"/"dist"
static=Path(os.environ.get("EVAL_LAB_STATIC",default_static))
if static.is_dir():
    app.mount("/",StaticFiles(directory=static,html=True),name="web")

