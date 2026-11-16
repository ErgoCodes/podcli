"""SSRF-safe URL opening: http(s) only, public addresses only, every redirect re-checked."""
from __future__ import annotations

import ipaddress
import socket
import urllib.error
import urllib.request
from urllib.parse import urlparse


def _is_public(ip_text: str) -> bool:
    ip = ipaddress.ip_address(ip_text.split("%", 1)[0])
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    return ip.is_global and not ip.is_multicast


def assert_public_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Unsupported URL scheme: {parsed.scheme or '(none)'}")
    host = (parsed.hostname or "").lower()
    if not host or host == "localhost" or host.endswith(".localhost"):
        raise ValueError(f"Refusing to fetch from a private/loopback host: {host or '(empty)'}")
    try:
        infos = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80))
    except socket.gaierror as exc:
        raise ValueError(f"Cannot resolve host {host}: {exc}") from exc
    if not infos or any(not _is_public(info[4][0]) for info in infos):
        raise ValueError(f"Refusing to fetch from a private/loopback host: {host}")


class _CheckedRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        assert_public_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def open_public_url(req: urllib.request.Request, timeout: float = 60):
    assert_public_url(req.full_url)
    opener = urllib.request.build_opener(_CheckedRedirects)
    return opener.open(req, timeout=timeout)
