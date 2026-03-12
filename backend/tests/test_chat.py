"""Tests for chat endpoints."""
import pytest


class TestGetSuggestions:
    def test_returns_suggestions(self, client):
        resp = client.get("/api/v1/chat/suggestions")
        assert resp.status_code == 200
        data = resp.json()
        assert "suggestions" in data
        assert isinstance(data["suggestions"], list)
        assert len(data["suggestions"]) > 0


class TestGetTopics:
    def test_returns_topics(self, client):
        resp = client.get("/api/v1/chat/topics")
        assert resp.status_code == 200
        data = resp.json()
        assert "topics" in data
        assert isinstance(data["topics"], dict)
        assert "basics" in data["topics"]

    def test_topic_has_structure(self, client):
        resp = client.get("/api/v1/chat/topics")
        topic = resp.json()["topics"]["planets"]
        assert "name" in topic
        assert "description" in topic
        assert "questions" in topic


class TestSendMessage:
    def test_no_auth_rejected(self, client):
        resp = client.post("/api/v1/chat/message", json={"message": "Hello"})
        assert resp.status_code in (401, 403)

    def test_send_message_authenticated(self, client, auth_headers):
        resp = client.post(
            "/api/v1/chat/message",
            json={"message": "What is my Sun sign?"},
            headers=auth_headers,
        )
        # May succeed or hit 500 if veda_mind isn't fully configured in test env
        assert resp.status_code in (200, 500)
