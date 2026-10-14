from app.services.deduplicate import content_hash_from_text, record_hash_from_job


def test_content_hash_stable() -> None:
    a = content_hash_from_text("hello   world")
    b = content_hash_from_text("hello world")
    assert a == b


def test_record_hash_ignores_unstable_fields() -> None:
    fields = {
        "job_code": "A01",
        "job_title": "科员",
        "city": "广州",
        "raw_data": '{"x": 1}',
    }
    h1 = record_hash_from_job({**fields, "raw_data": '{"x": 1}'})
    h2 = record_hash_from_job({**fields, "raw_data": '{"x": 2}'})
    assert h1 == h2
