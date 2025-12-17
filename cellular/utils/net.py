from __future__ import annotations

import ipaddress
import socket
from typing import Iterable, Optional, Tuple
from urllib.parse import urlparse


def is_allowed_snapshot_url(url: str, allowed_hosts: Iterable[str]) -> bool:
    """
    SSRF guard:
    - only http/https
    - hostname must be in allowlist
    - resolved IP must not be private/loopback/link-local/etc
    """
    try:
        parsed = urlparse(url)
    except Exception:
        return False

    if parsed.scheme not in ("http", "https"):
        return False

    hostname = parsed.hostname
    if not hostname:
        return False

    def normalize_allowed(entry: str) -> Tuple[str, Optional[int]]:
        entry = entry.strip().lower()
        if not entry:
            return ("", None)
        # Support "host:port" (common for IPv4/hostnames). For IPv6, prefer plain host allow.
        if entry.count(":") == 1:
            host_part, port_part = entry.split(":", 1)
            if port_part.isdigit():
                return (host_part, int(port_part))
        return (entry, None)

    allow: list[Tuple[str, Optional[int]]] = [
        normalize_allowed(h) for h in allowed_hosts if h and h.strip()
    ]

    if not allow:
        return False

    url_host = hostname.lower()
    url_port = parsed.port or (443 if parsed.scheme == "https" else 80)
    if not any((h == url_host and (p is None or p == url_port)) for (h, p) in allow):
        return False

    try:
        addrinfos = socket.getaddrinfo(
            hostname, parsed.port or (443 if parsed.scheme == "https" else 80)
        )
    except Exception:
        return False

    for ai in addrinfos:
        ip_str = ai[4][0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            return False
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_unspecified
            or ip.is_reserved
        ):
            return False

    return True
