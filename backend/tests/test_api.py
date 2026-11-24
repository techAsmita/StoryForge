"""Runs against the PostgreSQL DB in DATABASE_URL in demo mode (no API keys needed)."""
import os
import tempfile

os.environ["LLM_PROVIDER"] = "mock"
os.environ["IMAGE_PROVIDER"] = "placeholder"
os.environ["MEDIA_DIR"] = tempfile.mkdtemp()

import httpx
import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.providers import images

IDEA = {
    "protagonist": "A lone exorcist with forgotten powers",
    "goal": "Uncover the truth behind a shattered world",
    "genre": "Dark Fantasy",
    "world_rule": "Magic exists, but every spell has a deadly price",
    "ending_twist": "The real villain is the protagonist's future self",
}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.mark.parametrize("strategy,steps", [("direct", 1), ("interview", 2), ("cot", 1), ("tot", 2)])
def test_generate_each_strategy(client, strategy, steps, request):
    r = client.post("/api/stories/generate", json={"idea": IDEA, "strategy": strategy})
    assert r.status_code == 200, r.text
    body = r.json()
    request.addfinalizer(lambda: client.delete(f"/api/stories/{body['id']}"))
    assert len(body["runs"]) == steps
    assert len(body["output"]["beats"]) == 6
    assert IDEA["world_rule"] in body["runs"][-1]["prompt"]  # conditional generation
    assert body["metrics"]["structure_score"] == 1.0
    if strategy == "cot":
        assert "plan" in body["artifacts"]
    if strategy == "tot":
        assert body["artifacts"]["branches"]["selected"] in {"A", "B", "C"}
    # background image job has run (TestClient runs background tasks after the response)
    story = client.get(f"/api/stories/{body['id']}").json()
    assert [s["status"] for s in story["scenes"]] == ["ready"] * 4
    assert client.get(story["scenes"][0]["image_url"]).status_code == 200


def test_validation_rejects_bad_sampling(client):
    r = client.post("/api/stories/generate", json={"idea": IDEA, "sampling": {"temperature": 5}})
    assert r.status_code == 422


def test_library_favorite_rating_related_and_delete(client):
    a = client.post("/api/stories/generate", json={"idea": IDEA, "strategy": "direct"}).json()
    b = client.post("/api/stories/generate", json={"idea": IDEA, "strategy": "tot"}).json()
    assert a["idea_key"] == b["idea_key"]
    assert {s["id"] for s in client.get(f"/api/stories/{a['id']}/related").json()} >= {a["id"], b["id"]}

    r = client.patch(f"/api/stories/{a['id']}", json={
        "favorite": True,
        "human_rating": {"coherence": 4, "creativity": 5, "adherence": 4, "character_consistency": 3},
    })
    assert r.json()["favorite"] is True and r.json()["human_rating"]["creativity"] == 5

    summary = next(s for s in client.get("/api/stories").json() if s["id"] == a["id"])
    assert summary["favorite"] and summary["image_status"] == "ready" and summary["cover_url"]

    for sid in (a["id"], b["id"]):
        assert client.delete(f"/api/stories/{sid}").status_code == 204
    assert client.get(f"/api/stories/{a['id']}").status_code == 404


def test_settings_roundtrip(client):
    original = client.get("/api/settings").json()
    data = {**original, "strategy": "cot", "sampling": {**original["sampling"], "temperature": 0.4}}
    try:
        assert client.put("/api/settings", json=data).status_code == 200
        assert client.get("/api/settings").json()["sampling"]["temperature"] == 0.4
    finally:
        client.put("/api/settings", json=original)  # don't change the user's real defaults


def test_pollinations_retries_after_rate_limit(monkeypatch, tmp_path):
    """First call is rate limited (429), the retry succeeds and the file is saved."""
    monkeypatch.setattr(get_settings(), "image_provider", "pollinations")
    calls = []

    def fake_get(url, **kw):
        calls.append(url)
        if len(calls) == 1:
            return httpx.Response(429, request=httpx.Request("GET", url))
        return httpx.Response(200, content=b"\xff\xd8jpeg", headers={"content-type": "image/jpeg"},
                              request=httpx.Request("GET", url))

    monkeypatch.setattr(images.httpx, "get", fake_get)
    with pytest.raises(images.ImageError, match="rate_limited"):
        images.render_to_file("a castle", 1, "x", tmp_path / "s1")
    path = images.render_to_file("a castle", 1, "x", tmp_path / "s1")
    assert path.suffix == ".jpg" and path.read_bytes().startswith(b"\xff\xd8")
    assert "image.pollinations.ai" in calls[0]  # anonymous endpoint without a key


def test_openai_image_provider(monkeypatch, tmp_path):
    """OpenAI images: sends the key, picks a size from the aspect ratio, decodes base64 output."""
    import base64

    s = get_settings()
    monkeypatch.setattr(s, "image_provider", "openai")
    monkeypatch.setattr(s, "openai_api_key", "sk-test")
    sent = {}

    def fake_post(url, headers, json, timeout):
        sent.update(url=url, auth=headers["Authorization"], body=json)
        return httpx.Response(200, json={"data": [{"b64_json": base64.b64encode(b"\x89PNGdata").decode()}]},
                              request=httpx.Request("POST", url))

    monkeypatch.setattr(images.httpx, "post", fake_post)
    path = images.render_to_file("a castle", 1, "x", tmp_path / "s1")
    assert path.suffix == ".png" and path.read_bytes() == b"\x89PNGdata"
    assert sent["auth"] == "Bearer sk-test" and sent["body"]["model"] == s.openai_image_model
    assert images.fetch_image  # wide art picks the landscape size
    images.fetch_image("wide", 1600, 640, 1)
    assert sent["body"]["size"] == "1536x1024"
    assert images.min_interval() > 0


def test_openai_without_key_fails_clearly(monkeypatch, tmp_path):
    s = get_settings()
    monkeypatch.setattr(s, "image_provider", "openai")
    monkeypatch.setattr(s, "openai_api_key", "")
    with pytest.raises(images.ImageError, match="OPENAI_API_KEY"):
        images.render_to_file("a castle", 1, "x", tmp_path / "s1")
