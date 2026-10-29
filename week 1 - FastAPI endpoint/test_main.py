from fastapi.testclient import TestClient

import main


class FakeBedrockClient:
    def converse_stream(self, **kwargs):
        assert kwargs["messages"][0]["content"][0]["text"] == "Hello"
        return {
            "stream": iter([
                {"contentBlockDelta": {"delta": {"text": "Hello"}}},
                {"contentBlockDelta": {"delta": {"text": " world"}}},
                {"messageStop": {"stopReason": "end_turn"}},
            ])
        }


def test_health():
    with TestClient(main.app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_stream(monkeypatch):
    monkeypatch.setattr(main, "get_bedrock_client", lambda: FakeBedrockClient())

    with TestClient(main.app) as client:
        response = client.post("/chat/stream", json={"prompt": "Hello"})

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
    assert '"text": "Hello"' in response.text
    assert '"text": " world"' in response.text
    assert "event: done" in response.text


def test_validation_rejects_empty_prompt():
    with TestClient(main.app) as client:
        response = client.post("/chat/stream", json={"prompt": ""})
    assert response.status_code == 422
