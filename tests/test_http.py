import time

import httpx
import pytest

from tender_wazi.http import PoliteClient, UA


def make_client(handler, **kw):
    transport = httpx.MockTransport(handler)
    return PoliteClient(transport=transport, **kw)


def test_sends_an_identifying_user_agent():
    seen = {}

    def handler(request):
        seen["ua"] = request.headers.get("user-agent")
        return httpx.Response(200, text="ok")

    client = make_client(handler)
    client.get("https://example.test/tender")

    assert seen["ua"] == UA
    assert "tender-wazi" in seen["ua"]


def test_waits_the_minimum_interval_between_requests():
    calls = []

    def handler(request):
        calls.append(time.monotonic())
        return httpx.Response(200, text="ok")

    client = make_client(handler, min_interval=0.2)
    client.get("https://example.test/1")
    client.get("https://example.test/2")

    assert calls[1] - calls[0] >= 0.15


def test_retries_on_5xx_until_it_succeeds():
    attempts = []

    def handler(request):
        attempts.append(1)
        if len(attempts) < 3:
            return httpx.Response(503, text="busy")
        return httpx.Response(200, text="ok")

    client = make_client(handler, min_interval=0, retry_base=0)
    response = client.get("https://example.test/flaky")

    assert response.status_code == 200
    assert len(attempts) == 3


def test_honours_retry_after_on_429():
    attempts = []

    def handler(request):
        attempts.append(1)
        if len(attempts) == 1:
            return httpx.Response(429, headers={"Retry-After": "0"}, text="slow down")
        return httpx.Response(200, text="ok")

    client = make_client(handler, min_interval=0, retry_base=0)
    response = client.get("https://example.test/limited")

    assert response.status_code == 200
    assert len(attempts) == 2


def test_does_not_retry_a_4xx():
    attempts = []

    def handler(request):
        attempts.append(1)
        return httpx.Response(404, text="missing")

    client = make_client(handler, min_interval=0, retry_base=0)
    response = client.get("https://example.test/missing")

    assert response.status_code == 404
    assert len(attempts) == 1


def test_stops_at_the_page_cap():
    def handler(request):
        return httpx.Response(200, text="ok")

    client = make_client(handler, min_interval=0, max_pages=2)
    client.get("https://example.test/1")
    client.get("https://example.test/2")

    with pytest.raises(RuntimeError, match="page cap"):
        client.get("https://example.test/3")
