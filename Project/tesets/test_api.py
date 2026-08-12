from fastapi.testclient import TestClient

import backend.main as main_module

client = TestClient(main_module.app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_generate_starters(monkeypatch):
    monkeypatch.setattr(
        main_module.theme_extractor,
        "extract_themes",
        lambda text, extra_labels=None, top_k=3, score_threshold=0.15: ["artificial intelligence", "sustainability"],
    )
    monkeypatch.setattr(
        main_module.starter_generator,
        "generate_starters",
        lambda themes, interests, num_starters=3: ["Starter one?", "Starter two?", "Starter three?"][:num_starters],
    )
    monkeypatch.setattr(main_module.database, "add_history_entry", lambda *a, **k: 1)

    resp = client.post(
        "/api/generate-starters",
        json={
            "event_description": "AI for Sustainable Cities",
            "interests": ["climate change"],
            "num_starters": 2,
        },
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["themes"] == ["artificial intelligence", "sustainability"]
    assert len(data["starters"]) == 2


def test_generate_starters_validation_error():
    resp = client.post("/api/generate-starters", json={"event_description": "ok"})
    # event_description passes min_length=3, so this actually succeeds through
    # to generation; a genuinely invalid payload (missing field) is used below.
    resp2 = client.post("/api/generate-starters", json={"interests": ["ai"]})
    assert resp2.status_code == 422


def test_fact_check(monkeypatch):
    monkeypatch.setattr(
        main_module.fact_checker,
        "check",
        lambda query: {
            "query": query,
            "found": True,
            "summary": "Some reliable summary.",
            "url": "https://en.wikipedia.org/wiki/Test",
            "options": [],
        },
    )
    resp = client.post("/api/fact-check", json={"query": "test topic"})
    assert resp.status_code == 200
    assert resp.json()["found"] is True


def test_feedback_not_found(monkeypatch):
    monkeypatch.setattr(main_module.database, "update_feedback", lambda *a, **k: False)
    resp = client.post("/api/feedback", json={"history_id": 999, "useful": True})
    assert resp.status_code == 404


def test_history(monkeypatch):
    monkeypatch.setattr(
        main_module.database,
        "get_history",
        lambda limit=50: [
            {
                "id": 1,
                "event_description": "AI Summit",
                "interests": "ai",
                "themes": "artificial intelligence",
                "starter": "What excites you about AI?",
                "useful": 1,
                "created_at": "2026-01-01T00:00:00+00:00",
            }
        ],
    )
    resp = client.get("/api/history")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["useful"] is True
