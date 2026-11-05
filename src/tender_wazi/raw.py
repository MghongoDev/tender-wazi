import datetime as dt
import hashlib


def save_raw(conn, bucket, source: str, url: str, body: bytes, status: int) -> int:
    """Save the raw payload and record it in the manifest.

    The bytes are immutable: the key carries the fetch time and a content
    hash, so saving the same payload twice writes two objects.
    """
    ts = dt.datetime.now(dt.timezone.utc)
    sha = hashlib.sha256(body).hexdigest()
    key = f"raw/{source}/{ts:%Y/%m/%d}/{ts:%H%M%S}_{sha[:12]}.bin"
    bucket.put_object(Key=key, Body=body)
    row = conn.execute(
        "INSERT INTO raw_manifest (source, url, fetched_at, http_status, sha256, object_key) "
        "VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
        (source, url, ts, status, sha, key),
    ).fetchone()
    return row[0]
