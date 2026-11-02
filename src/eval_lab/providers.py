"""Explicitly configured provider adapters; Azure is not a runtime dependency."""
from __future__ import annotations
import asyncio
import os
import re
from contextlib import asynccontextmanager
from typing import Callable
import httpx
from agent_framework import Agent, tool
from .models import EndpointConnection
from .network import transport, validate_endpoint_url

def redact_secrets(value, keys):
    if isinstance(value,str):
        for key in keys:
            if key:
                value=value.replace(key,"[redacted]")
        return value
    if isinstance(value,list):
        return [redact_secrets(item,keys) for item in value]
    if isinstance(value,dict):
        return {key:redact_secrets(item,keys) for key,item in value.items()}
    return value

def credential(connection: EndpointConnection, hosted: bool) -> str | None:
    if connection.definition.authentication.type == "none":
        return None
    key = connection.api_key.get_secret_value() if connection.api_key else None
    variable = connection.definition.authentication.environment_variable
    if not key and variable and not hosted:
        key = os.environ.get(variable)
    if not key:
        raise ValueError("This connection requires an API key. Enter it for this session.")
    return key

def safe_error(error: Exception, keys: list[str] | None = None) -> str:
    """Never surface SDK request headers, bodies, tracebacks, or key material."""
    if isinstance(error, ValueError):
        value = str(error)[:400]
        for key in keys or []:
            if key:
                value = value.replace(key, "[redacted]")
        return re.sub(r"(?i)(bearer\s+|api[_-]?key[=: ]+)\S+", "[redacted]", value)
    name = type(error).__name__
    causes = []
    current = error
    while current is not None and len(causes)<5:
        causes.append(type(current).__name__)
        current = current.__cause__ or current.__context__
    name = " ".join(causes)
    if "Authentication" in name or "Permission" in name:
        return "The endpoint rejected authentication or access. Check the connection settings."
    if "Timeout" in name:
        return "The model endpoint exceeded the configured time limit."
    if "Connect" in name or "Network" in name:
        return "The model endpoint could not be reached from this runner."
    if "RateLimit" in name:
        return "The model endpoint reported a rate limit."
    return f"The model or evaluator failed ({name}). No secret-bearing provider response is exported."

@asynccontextmanager
async def openai_adapter(connection: EndpointConnection, hosted: bool):
    from openai import AsyncOpenAI
    from agent_framework_openai import OpenAIChatCompletionClient
    d = connection.definition
    key = credential(connection, hosted)
    async def remove_unused_auth(request):
        if key is None:
            request.headers.pop("Authorization",None)
    http = httpx.AsyncClient(transport=transport(hosted), follow_redirects=False, trust_env=False,
        event_hooks={"request":[remove_unused_auth]})
    sdk = AsyncOpenAI(api_key=key or "local-no-key", base_url=d.base_url,
        http_client=http, timeout=d.generation.timeout_seconds, max_retries=0)
    client = OpenAIChatCompletionClient(model=d.model, async_client=sdk,
        instruction_role="system",
        function_invocation_configuration={"max_iterations":6,"max_function_calls":12,"max_duration_seconds":120})
    try:
        yield client
    finally:
        await sdk.close()

@asynccontextmanager
async def ollama_adapter(connection: EndpointConnection, hosted: bool):
    import ollama
    from agent_framework_ollama import OllamaChatClient
    d = connection.definition
    key = credential(connection, hosted)
    sdk = ollama.AsyncClient(host=d.base_url, transport=transport(hosted),
        headers={"Authorization":f"Bearer {key}"} if key else {},
        timeout=httpx.Timeout(d.generation.timeout_seconds), follow_redirects=False, trust_env=False)
    client = OllamaChatClient(host=d.base_url, model=d.model, client=sdk,
        function_invocation_configuration={"max_iterations":6,"max_function_calls":12,"max_duration_seconds":120})
    try:
        yield client
    finally:
        await sdk._client.aclose()  # ollama 0.5.3 exposes no public close method.

ADAPTERS: dict[str, Callable] = {
    "openai_chat_completions": openai_adapter,
    "ollama": ollama_adapter,
}

def register_adapter(protocol: str, factory: Callable) -> None:
    """Install a trusted Python adapter, never uploaded executable config."""
    if not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", protocol):
        raise ValueError("Invalid adapter protocol name.")
    ADAPTERS[protocol] = factory

@asynccontextmanager
async def model_client(connection: EndpointConnection, hosted: bool):
    validate_endpoint_url(connection.definition.base_url, hosted)
    adapter = ADAPTERS.get(connection.definition.protocol)
    if adapter is None:
        raise ValueError("This endpoint protocol has no installed adapter.")
    async with adapter(connection, hosted) as client:
        yield client

def generation_options(connection: EndpointConnection) -> dict:
    d = connection.definition.generation
    result = {"max_tokens":d.max_output_tokens}
    if d.temperature is not None:
        result["temperature"] = d.temperature
    return result

async def test_connection(connection: EndpointConnection, hosted: bool) -> dict:
    """Probe actual text generation and a harmless function round trip."""
    called = []
    @tool(approval_mode="never_require")
    async def endpoint_probe(value: str) -> dict:
        """Echo the literal string evaluation-lab to test a function round trip."""
        called.append(value)
        return {"echo":value}

    async with model_client(connection, hosted) as client:
        agent = Agent(client=client, name="connection-test", tools=[endpoint_probe],
            instructions="Call endpoint_probe with value evaluation-lab. After its result, reply connected.",
            default_options={"max_tokens":128})
        try:
            async with asyncio.timeout(connection.definition.generation.timeout_seconds):
                result = await agent.run("Test the connection now by calling endpoint_probe.")
            return {"connected":bool(result.text or called), "tools": "evaluation-lab" in called,
                "message": "Text and function calling verified." if "evaluation-lab" in called
                    else "Text generation worked, but this model did not demonstrate function calling. Tool exercises are disabled.",
                "protocol":connection.definition.protocol, "model":connection.definition.model}
        finally:
            await agent.close()

