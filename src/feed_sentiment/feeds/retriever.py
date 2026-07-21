from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass, field
from typing import Protocol
from urllib.parse import urljoin, urlsplit

import httpx

from feed_sentiment._metadata import default_user_agent
from feed_sentiment.exceptions import (
    ContentTypeError,
    ResponseSizeError,
    RetrievalError,
    UnsafeUrlError,
)


@dataclass(frozen=True, slots=True)
class RetrievalPolicy:
    connect_timeout: float = 5.0
    read_timeout: float = 15.0
    max_redirects: int = 5
    max_response_bytes: int = 5 * 1024 * 1024
    allow_private_networks: bool = False
    user_agent: str = field(default_factory=default_user_agent)


@dataclass(frozen=True, slots=True)
class RetrievedFeed:
    url: str
    content: bytes
    content_type: str | None


class FeedRetriever(Protocol):
    def fetch(self, url: str, policy: RetrievalPolicy) -> RetrievedFeed: ...


def _blocked(address: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    return any(
        (
            address.is_private,
            address.is_loopback,
            address.is_link_local,
            address.is_multicast,
            address.is_unspecified,
            address.is_reserved,
        )
    )


def validate_url(url: str, policy: RetrievalPolicy) -> None:
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"}:
        raise UnsafeUrlError(url, "Only HTTP and HTTPS feed URLs are allowed")
    if not parsed.hostname or parsed.username is not None or parsed.password is not None:
        raise UnsafeUrlError(url, "Feed URL must have a host and no embedded credentials")
    if policy.allow_private_networks:
        return
    try:
        infos = socket.getaddrinfo(parsed.hostname, parsed.port, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise RetrievalError(url, f"Could not resolve feed host ({exc})") from exc
    for info in infos:
        address = ipaddress.ip_address(info[4][0])
        if _blocked(address):
            raise UnsafeUrlError(url, f"Feed URL resolves to blocked address {address}")


_ACCEPTED_TYPES = {
    "application/atom+xml",
    "application/rss+xml",
    "application/xml",
    "text/xml",
    "application/octet-stream",
    "binary/octet-stream",
}


class HttpxFeedRetriever:
    def fetch(self, url: str, policy: RetrievalPolicy) -> RetrievedFeed:
        current = url
        timeout = httpx.Timeout(policy.read_timeout, connect=policy.connect_timeout)
        try:
            with httpx.Client(
                follow_redirects=False, timeout=timeout, headers={"User-Agent": policy.user_agent}
            ) as client:
                for redirect_count in range(policy.max_redirects + 1):
                    validate_url(current, policy)
                    with client.stream("GET", current) as response:
                        if response.is_redirect:
                            location = response.headers.get("location")
                            if not location or redirect_count >= policy.max_redirects:
                                raise RetrievalError(
                                    current, "Feed redirect limit exceeded or target missing"
                                )
                            current = urljoin(current, location)
                            continue
                        response.raise_for_status()
                        media_type = (
                            response.headers.get("content-type", "")
                            .split(";", 1)[0]
                            .strip()
                            .lower()
                        )
                        if (
                            media_type
                            and media_type not in _ACCEPTED_TYPES
                            and not media_type.endswith("+xml")
                        ):
                            raise ContentTypeError(
                                current, f"Unsupported feed content type {media_type}"
                            )
                        chunks: list[bytes] = []
                        size = 0
                        for chunk in response.iter_bytes():
                            size += len(chunk)
                            if size > policy.max_response_bytes:
                                raise ResponseSizeError(
                                    current,
                                    f"Feed response exceeds {policy.max_response_bytes} bytes",
                                )
                            chunks.append(chunk)
                        return RetrievedFeed(
                            str(response.url), b"".join(chunks), media_type or None
                        )
        except RetrievalError:
            raise
        except httpx.TimeoutException as exc:
            raise RetrievalError(current, "Feed retrieval timed out") from exc
        except httpx.HTTPError as exc:
            raise RetrievalError(current, f"Feed retrieval failed ({exc})") from exc
        raise RetrievalError(current, "Feed redirect handling failed")
