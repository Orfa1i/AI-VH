"""
Global pytest configuration and network-blocking test fixtures for AI-VH.
Enforces zero external network calls during automated test execution.
"""

import socket
import pytest
from typing import Any, Tuple

ALLOWED_HOSTS = {"127.0.0.1", "::1", "localhost", "0.0.0.0"}


@pytest.fixture(autouse=True)
def block_external_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Network-blocking fixture to ensure 100% offline test execution.
    Intercepts socket connections and DNS resolution to non-local endpoints.
    """
    orig_connect = socket.socket.connect
    orig_getaddrinfo = socket.getaddrinfo

    def guarded_connect(self: socket.socket, address: Any) -> Any:
        host = address[0] if isinstance(address, tuple) and len(address) > 0 else str(address)
        if host not in ALLOWED_HOSTS:
            raise RuntimeError(
                f"Live network call blocked by AI-VH test fixture: attempted connection to {host}"
            )
        return orig_connect(self, address)

    def guarded_getaddrinfo(host: Any, port: Any, *args: Any, **kwargs: Any) -> Any:
        if host and str(host).lower() not in ALLOWED_HOSTS:
            raise RuntimeError(
                f"Live network call blocked by AI-VH test fixture: DNS lookup for {host}"
            )
        return orig_getaddrinfo(host, port, *args, **kwargs)

    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    monkeypatch.setattr(socket, "getaddrinfo", guarded_getaddrinfo)
