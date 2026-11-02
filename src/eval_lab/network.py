"""Pin public DNS resolutions to their checked IPs for hosted model requests."""
from __future__ import annotations
import asyncio
import ipaddress
import socket
from urllib.parse import urlsplit
import httpcore
import httpx

def public_address(value: str) -> bool:
    address = ipaddress.ip_address(value)
    return address.is_global and not (address.is_multicast or address.is_reserved or address.is_unspecified)

def validate_endpoint_url(value: str, hosted: bool) -> None:
    url = urlsplit(value)
    if url.scheme not in {"http","https"} or not url.hostname or url.username or url.password or url.fragment or url.query:
        raise ValueError("Use an HTTP(S) base URL without embedded credentials, query strings, or fragments.")
    if hosted and (url.scheme != "https" or url.port not in {None,443}):
        raise ValueError("Hosted connections require a public HTTPS endpoint on port 443. Use the local runner for private endpoints.")
    if hosted:
        try:
            address = ipaddress.ip_address(url.hostname)
        except ValueError:
            if url.hostname.lower()=="localhost" or url.hostname.lower().endswith((".localhost",".local",".internal")):
                raise ValueError("Local endpoints belong in the downloadable local runner.")
        else:
            if not public_address(str(address)):
                raise ValueError("Private and reserved addresses are unavailable from the hosted service.")

class PublicNetworkBackend(httpcore.AsyncNetworkBackend):
    """Connect to the validated IP itself; TLS SNI still uses the original host."""
    def __init__(self):
        self.backend = httpcore.AnyIOBackend()

    async def connect_tcp(self,host,port,timeout=None,local_address=None,socket_options=None):
        if port != 443:
            raise ValueError("Only public HTTPS model endpoints are available in hosted mode.")
        records = await asyncio.get_running_loop().getaddrinfo(host,port,type=socket.SOCK_STREAM)
        addresses = list(dict.fromkeys(record[4][0] for record in records))
        if not addresses or any(not public_address(address) for address in addresses):
            raise ValueError("The model endpoint resolved to a private or reserved address.")
        last_error = None
        for address in addresses:
            try:
                return await self.backend.connect_tcp(address,port,timeout,local_address,socket_options)
            except (httpcore.ConnectError,httpcore.ConnectTimeout) as error:
                last_error = error
        raise last_error or ValueError("The endpoint has no usable public address.")

    async def connect_unix_socket(self,*args,**kwargs):
        raise ValueError("Unix sockets are unavailable in hosted mode.")

    async def sleep(self,seconds):
        await asyncio.sleep(seconds)

def transport(hosted: bool) -> httpx.AsyncHTTPTransport:
    result = httpx.AsyncHTTPTransport(retries=0)
    if hosted:
        # httpx has no public constructor parameter for a custom network backend.
        # Covered by DNS pinning tests and the locked httpx/httpcore versions.
        result._pool = httpcore.AsyncConnectionPool(network_backend=PublicNetworkBackend(),retries=0)
    return result

