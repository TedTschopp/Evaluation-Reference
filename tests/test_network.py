import asyncio
import socket
import pytest
from eval_lab.network import PublicNetworkBackend,public_address,validate_endpoint_url

@pytest.mark.parametrize("url",[
    "http://example.com/v1","https://127.0.0.1/v1","https://[::1]/v1","https://localhost/v1",
    "https://service.internal/v1","https://169.254.169.254/v1","https://10.0.0.1/v1",
    "https://user:secret@example.com/v1","https://example.com:8443/v1","https://example.com/v1?api_key=secret",
    "file:///etc/passwd","https://224.0.0.1/v1"])
def test_hosted_rejects_private_or_credential_urls(url):
    with pytest.raises(ValueError):validate_endpoint_url(url,True)

def test_local_mode_accepts_local_endpoints():
    validate_endpoint_url("http://localhost:11434",False)
    validate_endpoint_url("http://10.1.2.3:8000/v1",False)
    validate_endpoint_url("https://models.example/v1",True)

@pytest.mark.asyncio
async def test_dns_is_pinned_to_checked_ip(monkeypatch):
    backend=PublicNetworkBackend();connections=[]
    async def resolve(*args,**kwargs):
        return [(socket.AF_INET,socket.SOCK_STREAM,6,"",("1.1.1.1",443))]
    async def connect(host,*args):
        connections.append(host);return object()
    monkeypatch.setattr(asyncio.get_running_loop(),"getaddrinfo",resolve)
    monkeypatch.setattr(backend.backend,"connect_tcp",connect)
    await backend.connect_tcp("public.example",443)
    assert connections==["1.1.1.1"]

@pytest.mark.asyncio
async def test_dns_mixed_public_private_is_rejected(monkeypatch):
    backend=PublicNetworkBackend()
    async def resolve(*args,**kwargs):
        return [(socket.AF_INET,socket.SOCK_STREAM,6,"",("1.1.1.1",443)),
            (socket.AF_INET,socket.SOCK_STREAM,6,"",("127.0.0.1",443))]
    monkeypatch.setattr(asyncio.get_running_loop(),"getaddrinfo",resolve)
    with pytest.raises(ValueError,match="private"):
        await backend.connect_tcp("rebinding.example",443)

@pytest.mark.parametrize("ip",["224.0.0.1","0.0.0.0","127.0.0.1","169.254.169.254","192.168.1.2","::1","ff02::1"])
def test_non_public_address_classes(ip):
    assert not public_address(ip)

