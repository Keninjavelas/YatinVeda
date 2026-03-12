"""Tests for MFA setup, enable, disable, backup-codes, and trusted-devices endpoints."""

import pytest
from unittest.mock import patch, MagicMock
import pyotp

from models.database import MFASettings


class TestMFAStatus:
    def test_status_no_mfa(self, client, test_user, auth_headers):
        response = client.get("/api/v1/mfa/status", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["is_enabled"] is False
        assert data["backup_codes_status"] is None

    def test_status_unauthenticated(self, client):
        response = client.get("/api/v1/mfa/status")
        assert response.status_code in (401, 403)


class TestMFASetup:
    def test_setup_returns_qr_and_codes(self, client, test_user, auth_headers):
        response = client.post("/api/v1/mfa/setup", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "qr_code" in data
        assert "secret_key" in data
        assert "backup_codes" in data
        assert len(data["backup_codes"]) > 0

    def test_setup_twice_resets(self, client, test_user, auth_headers):
        r1 = client.post("/api/v1/mfa/setup", headers=auth_headers)
        assert r1.status_code == 200
        r2 = client.post("/api/v1/mfa/setup", headers=auth_headers)
        assert r2.status_code == 200
        # Second setup should give a different secret
        assert r1.json()["secret_key"] != r2.json()["secret_key"]

    def test_setup_already_enabled_blocked(self, client, test_user, auth_headers):
        # Setup and enable MFA
        setup = client.post("/api/v1/mfa/setup", headers=auth_headers)
        secret = setup.json()["secret_key"]
        totp = pyotp.TOTP(secret)
        code = totp.now()
        client.post("/api/v1/mfa/enable", headers=auth_headers, json={"code": code})

        # Try to setup again — should be blocked
        response = client.post("/api/v1/mfa/setup", headers=auth_headers)
        assert response.status_code == 400


class TestMFAEnable:
    def test_enable_with_valid_code(self, client, test_user, auth_headers):
        setup = client.post("/api/v1/mfa/setup", headers=auth_headers)
        secret = setup.json()["secret_key"]
        totp = pyotp.TOTP(secret)
        code = totp.now()

        response = client.post(
            "/api/v1/mfa/enable", headers=auth_headers, json={"code": code}
        )
        assert response.status_code == 200
        assert response.json()["is_enabled"] is True

    def test_enable_with_invalid_code(self, client, test_user, auth_headers):
        client.post("/api/v1/mfa/setup", headers=auth_headers)
        response = client.post(
            "/api/v1/mfa/enable", headers=auth_headers, json={"code": "000000"}
        )
        assert response.status_code == 400


class TestMFADisable:
    def _enable_mfa(self, client, auth_headers):
        setup = client.post("/api/v1/mfa/setup", headers=auth_headers)
        secret = setup.json()["secret_key"]
        totp = pyotp.TOTP(secret)
        code = totp.now()
        client.post("/api/v1/mfa/enable", headers=auth_headers, json={"code": code})
        return secret

    def test_disable_mfa(self, client, test_user, auth_headers):
        secret = self._enable_mfa(client, auth_headers)
        totp = pyotp.TOTP(secret)
        code = totp.now()
        response = client.post(
            "/api/v1/mfa/disable", headers=auth_headers, json={"code": code}
        )
        assert response.status_code == 200
        assert response.json()["is_enabled"] is False

    def test_disable_without_mfa_fails(self, client, test_user, auth_headers):
        response = client.post(
            "/api/v1/mfa/disable", headers=auth_headers, json={"code": None}
        )
        assert response.status_code == 400


class TestBackupCodes:
    def _enable_mfa(self, client, auth_headers):
        setup = client.post("/api/v1/mfa/setup", headers=auth_headers)
        secret = setup.json()["secret_key"]
        totp = pyotp.TOTP(secret)
        code = totp.now()
        client.post("/api/v1/mfa/enable", headers=auth_headers, json={"code": code})

    def test_backup_status_no_mfa(self, client, test_user, auth_headers):
        response = client.get("/api/v1/mfa/backup-codes/status", headers=auth_headers)
        assert response.status_code == 400

    def test_backup_status_with_mfa(self, client, test_user, auth_headers):
        self._enable_mfa(client, auth_headers)
        response = client.get("/api/v1/mfa/backup-codes/status", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["remaining"] > 0

    def test_regenerate_no_mfa(self, client, test_user, auth_headers):
        response = client.post("/api/v1/mfa/backup-codes/regenerate", headers=auth_headers)
        assert response.status_code == 400

    def test_regenerate_with_mfa(self, client, test_user, auth_headers):
        self._enable_mfa(client, auth_headers)
        response = client.post("/api/v1/mfa/backup-codes/regenerate", headers=auth_headers)
        assert response.status_code == 200
        codes = response.json()
        assert len(codes) > 0


class TestTrustedDevices:
    def _enable_mfa(self, client, auth_headers):
        setup = client.post("/api/v1/mfa/setup", headers=auth_headers)
        secret = setup.json()["secret_key"]
        totp = pyotp.TOTP(secret)
        code = totp.now()
        client.post("/api/v1/mfa/enable", headers=auth_headers, json={"code": code})

    def test_list_devices_no_mfa(self, client, test_user, auth_headers):
        response = client.get("/api/v1/mfa/devices", headers=auth_headers)
        assert response.status_code == 400

    def test_list_devices_empty(self, client, test_user, auth_headers):
        self._enable_mfa(client, auth_headers)
        response = client.get("/api/v1/mfa/devices", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_revoke_nonexistent_device(self, client, test_user, auth_headers):
        self._enable_mfa(client, auth_headers)
        response = client.delete("/api/v1/mfa/devices/99999", headers=auth_headers)
        assert response.status_code == 404
