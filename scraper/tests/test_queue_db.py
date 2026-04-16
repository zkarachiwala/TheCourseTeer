"""Integration tests for scrape queue DB functions."""
import pytest
from db import (
    complete_run,
    enqueue_urls,
    get_or_create_run,
    get_pending_urls,
    mark_discovery_complete,
    mark_url_complete,
    mark_url_failed,
)


async def test_get_or_create_run_creates_first_run(pool, university_id):
    run = await get_or_create_run(pool, university_id, force=False)
    assert run["run_number"] == 1
    assert run["status"] == "in_progress"
    assert run["discovery_complete"] is False
    assert run["forced"] is False


async def test_get_or_create_run_resumes_existing(pool, university_id):
    run1 = await get_or_create_run(pool, university_id, force=False)
    run2 = await get_or_create_run(pool, university_id, force=False)
    assert run1["id"] == run2["id"]


async def test_get_or_create_run_increments_on_force(pool, university_id):
    await get_or_create_run(pool, university_id, force=False)
    run2 = await get_or_create_run(pool, university_id, force=True)
    assert run2["run_number"] == 2
    assert run2["forced"] is True


async def test_force_deletes_queue_rows(pool, university_id):
    run1 = await get_or_create_run(pool, university_id, force=False)
    await enqueue_urls(pool, university_id, str(run1["id"]), ["https://example.com/a"])
    await get_or_create_run(pool, university_id, force=True)
    pending = await get_pending_urls(pool, university_id)
    assert pending == []


async def test_enqueue_urls_inserts_pending(pool, university_id):
    run = await get_or_create_run(pool, university_id, force=False)
    urls = ["https://example.com/a", "https://example.com/b"]
    await enqueue_urls(pool, university_id, str(run["id"]), urls)
    pending = await get_pending_urls(pool, university_id)
    assert set(pending) == set(urls)


async def test_enqueue_urls_is_idempotent(pool, university_id):
    run = await get_or_create_run(pool, university_id, force=False)
    url = "https://example.com/a"
    await enqueue_urls(pool, university_id, str(run["id"]), [url])
    await enqueue_urls(pool, university_id, str(run["id"]), [url])
    pending = await get_pending_urls(pool, university_id)
    assert pending.count(url) == 1


async def test_mark_url_complete_removes_from_pending(pool, university_id):
    run = await get_or_create_run(pool, university_id, force=False)
    run_id = str(run["id"])
    await enqueue_urls(pool, university_id, run_id, ["https://example.com/a"])
    await mark_url_complete(pool, university_id, "https://example.com/a", run_id)
    pending = await get_pending_urls(pool, university_id)
    assert pending == []


async def test_mark_url_failed_increments_attempt(pool, university_id):
    run = await get_or_create_run(pool, university_id, force=False)
    url = "https://example.com/a"
    await enqueue_urls(pool, university_id, str(run["id"]), [url])
    await mark_url_failed(pool, university_id, url, "timeout")
    # Still pending (attempt_count=1 < max_attempts=3)
    pending = await get_pending_urls(pool, university_id, max_attempts=3)
    assert url in pending


async def test_mark_url_failed_three_times_marks_failed(pool, university_id):
    run = await get_or_create_run(pool, university_id, force=False)
    url = "https://example.com/a"
    await enqueue_urls(pool, university_id, str(run["id"]), [url])
    for _ in range(3):
        await mark_url_failed(pool, university_id, url, "timeout", max_attempts=3)
    pending = await get_pending_urls(pool, university_id, max_attempts=3)
    assert url not in pending


async def test_complete_run_sets_status(pool, university_id):
    run = await get_or_create_run(pool, university_id, force=False)
    await complete_run(pool, str(run["id"]))
    # A new call without force should create a new run (old one is complete)
    run2 = await get_or_create_run(pool, university_id, force=False)
    assert run2["id"] != run["id"]
    assert run2["run_number"] == 2
