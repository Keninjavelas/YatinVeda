"""Tests for community endpoints (posts, comments, likes, follows, events)."""
import pytest
from datetime import datetime, timedelta


class TestPosts:
    def test_create_post(self, client, auth_headers):
        resp = client.post(
            "/api/v1/community/posts",
            json={"content": "Hello community!", "post_type": "text"},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["content"] == "Hello community!"
        assert data["post_type"] == "text"
        assert data["is_own_post"] is True

    def test_create_post_no_auth(self, client):
        resp = client.post("/api/v1/community/posts", json={"content": "test"})
        assert resp.status_code in (401, 403)

    def test_create_post_empty_content(self, client, auth_headers):
        resp = client.post(
            "/api/v1/community/posts",
            json={"content": ""},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_get_feed(self, client, auth_headers):
        # Create a post first
        client.post(
            "/api/v1/community/posts",
            json={"content": "Feed post"},
            headers=auth_headers,
        )
        resp = client.get("/api/v1/community/posts?feed_type=public", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_get_post_by_id(self, client, auth_headers):
        create_resp = client.post(
            "/api/v1/community/posts",
            json={"content": "A specific post"},
            headers=auth_headers,
        )
        post_id = create_resp.json()["id"]
        resp = client.get(f"/api/v1/community/posts/{post_id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["content"] == "A specific post"

    def test_get_post_not_found(self, client, auth_headers):
        resp = client.get("/api/v1/community/posts/99999", headers=auth_headers)
        assert resp.status_code == 404

    def test_update_post(self, client, auth_headers):
        create_resp = client.post(
            "/api/v1/community/posts",
            json={"content": "Original post"},
            headers=auth_headers,
        )
        post_id = create_resp.json()["id"]
        resp = client.put(
            f"/api/v1/community/posts/{post_id}",
            json={"content": "Updated post"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["content"] == "Updated post"

    def test_delete_post(self, client, auth_headers):
        create_resp = client.post(
            "/api/v1/community/posts",
            json={"content": "Delete me"},
            headers=auth_headers,
        )
        post_id = create_resp.json()["id"]
        resp = client.delete(f"/api/v1/community/posts/{post_id}", headers=auth_headers)
        assert resp.status_code == 204

    def test_delete_post_not_owner(self, client, auth_headers, second_auth_headers):
        create_resp = client.post(
            "/api/v1/community/posts",
            json={"content": "Not yours"},
            headers=auth_headers,
        )
        post_id = create_resp.json()["id"]
        resp = client.delete(f"/api/v1/community/posts/{post_id}", headers=second_auth_headers)
        assert resp.status_code == 403


class TestLikes:
    def _create_post(self, client, auth_headers):
        resp = client.post(
            "/api/v1/community/posts",
            json={"content": "Likeable post"},
            headers=auth_headers,
        )
        return resp.json()["id"]

    def test_like_post(self, client, auth_headers, second_auth_headers, second_test_user):
        post_id = self._create_post(client, auth_headers)
        resp = client.post(f"/api/v1/community/posts/{post_id}/like", headers=second_auth_headers)
        assert resp.status_code == 201

    def test_unlike_post(self, client, auth_headers, second_auth_headers, second_test_user):
        post_id = self._create_post(client, auth_headers)
        client.post(f"/api/v1/community/posts/{post_id}/like", headers=second_auth_headers)
        resp = client.delete(f"/api/v1/community/posts/{post_id}/like", headers=second_auth_headers)
        assert resp.status_code == 200

    def test_like_nonexistent_post(self, client, auth_headers):
        resp = client.post("/api/v1/community/posts/99999/like", headers=auth_headers)
        assert resp.status_code == 404


class TestComments:
    def _create_post(self, client, auth_headers):
        resp = client.post(
            "/api/v1/community/posts",
            json={"content": "Commentable post"},
            headers=auth_headers,
        )
        return resp.json()["id"]

    def test_create_comment(self, client, auth_headers):
        post_id = self._create_post(client, auth_headers)
        resp = client.post(
            f"/api/v1/community/posts/{post_id}/comments",
            json={"content": "Nice post!"},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["content"] == "Nice post!"

    def test_get_comments(self, client, auth_headers):
        post_id = self._create_post(client, auth_headers)
        client.post(
            f"/api/v1/community/posts/{post_id}/comments",
            json={"content": "Comment 1"},
            headers=auth_headers,
        )
        resp = client.get(f"/api/v1/community/posts/{post_id}/comments", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_delete_comment(self, client, auth_headers):
        post_id = self._create_post(client, auth_headers)
        comment_resp = client.post(
            f"/api/v1/community/posts/{post_id}/comments",
            json={"content": "Remove me"},
            headers=auth_headers,
        )
        comment_id = comment_resp.json()["id"]
        resp = client.delete(f"/api/v1/community/comments/{comment_id}", headers=auth_headers)
        assert resp.status_code == 204


class TestFollows:
    def test_follow_user(self, client, auth_headers, second_test_user):
        resp = client.post(f"/api/v1/community/users/{second_test_user.id}/follow", headers=auth_headers)
        assert resp.status_code == 201

    def test_unfollow_user(self, client, auth_headers, second_test_user):
        client.post(f"/api/v1/community/users/{second_test_user.id}/follow", headers=auth_headers)
        resp = client.delete(f"/api/v1/community/users/{second_test_user.id}/follow", headers=auth_headers)
        assert resp.status_code == 200

    def test_get_user_profile(self, client, auth_headers, test_user):
        resp = client.get(f"/api/v1/community/users/{test_user.id}/profile", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == test_user.id


class TestEvents:
    def _event_data(self):
        return {
            "title": "Full Moon Meditation",
            "description": "Join us for a group meditation.",
            "event_type": "ritual",
            "event_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "duration_minutes": 60,
            "is_public": True,
        }

    def test_create_event(self, client, auth_headers):
        resp = client.post("/api/v1/community/events", json=self._event_data(), headers=auth_headers)
        assert resp.status_code == 201
        assert resp.json()["title"] == "Full Moon Meditation"

    def test_get_events(self, client, auth_headers):
        client.post("/api/v1/community/events", json=self._event_data(), headers=auth_headers)
        resp = client.get("/api/v1/community/events", headers=auth_headers)
        assert resp.status_code == 200

    def test_register_for_event(self, client, auth_headers, second_auth_headers, second_test_user):
        event_resp = client.post("/api/v1/community/events", json=self._event_data(), headers=auth_headers)
        event_id = event_resp.json()["id"]
        resp = client.post(f"/api/v1/community/events/{event_id}/register", headers=second_auth_headers)
        assert resp.status_code == 201


class TestNotifications:
    def test_get_notifications(self, client, auth_headers):
        resp = client.get("/api/v1/community/notifications", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
