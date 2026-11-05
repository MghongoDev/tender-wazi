import time

import httpx

UA = "tender-wazi/0.1 (+https://github.com/MghongoDev/tender-wazi; contact: mwandairodavid@gmail.com)"

# Client(transport=...) and MockTransport:
# https://www.python-httpx.org/advanced/transports/
# https://www.python-httpx.org/testing/


class PoliteClient:
    """One HTTP client for every source.

    Sends an identifying User-Agent, waits a minimum interval between
    requests, retries 429 and 5xx with backoff, honours Retry-After, and
    stops at a hard page cap. A response that is not retryable is returned
    as-is, so the caller decides what a 4xx means.
    """

    def __init__(
        self,
        min_interval: float = 2.0,
        max_pages: int | None = None,
        retry_base: float = 5.0,
        transport: httpx.BaseTransport | None = None,
    ):
        self.c = httpx.Client(
            headers={"User-Agent": UA},
            timeout=30,
            follow_redirects=True,
            transport=transport,
        )
        self.min_interval = min_interval
        self.max_pages = max_pages
        self.retry_base = retry_base
        self._last = 0.0
        self.pages = 0

    def get(self, url: str, **kw) -> httpx.Response:
        if self.max_pages is not None and self.pages >= self.max_pages:
            raise RuntimeError("page cap reached")
        wait = self.min_interval - (time.monotonic() - self._last)
        if wait > 0:
            time.sleep(wait)
        retries = 0
        while True:
            response = self.c.get(url, **kw)
            self._last = time.monotonic()
            self.pages += 1
            retryable = response.status_code in (429, 500, 502, 503, 504)
            if not retryable:
                return response
            if retries < 3:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else self.retry_base * 2 ** retries
                retries += 1
                time.sleep(delay)
                continue
            response.raise_for_status()
            return response
