import hashlib

from tender_wazi.raw import save_raw


class FakeConn:
    def __init__(self, row=(42,)):
        self.row = row
        self.executed = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        return self

    def fetchone(self):
        return self.row


class FakeBucket:
    def __init__(self):
        self.objects = []

    def put_object(self, Key, Body):
        self.objects.append((Key, Body))


def test_save_raw_writes_the_object_and_records_the_manifest_row():
    conn = FakeConn()
    bucket = FakeBucket()
    body = b'{"ocid": "ocds-5whusi-1"}'

    raw_id = save_raw(conn, bucket, "ppip", "https://example.test/2025.jsonl.gz", body, 200)

    assert raw_id == 42
    assert len(bucket.objects) == 1
    key, saved_body = bucket.objects[0]
    assert key.startswith("raw/ppip/")
    assert key.endswith(".bin")
    assert saved_body == body

    sql, params = conn.executed[0]
    assert "INSERT INTO raw_manifest" in sql
    source, url, fetched_at, status, sha, object_key = params
    assert source == "ppip"
    assert url == "https://example.test/2025.jsonl.gz"
    assert status == 200
    assert sha == hashlib.sha256(body).hexdigest()
    assert object_key == key
    assert fetched_at.tzinfo is not None


def test_save_raw_key_carries_the_source_and_a_content_hash():
    conn = FakeConn()
    bucket = FakeBucket()

    save_raw(conn, bucket, "portal_b", "https://example.test/listing", b"<html></html>", 200)

    key, _ = bucket.objects[0]
    assert key.startswith("raw/portal_b/")
    assert hashlib.sha256(b"<html></html>").hexdigest()[:12] in key
