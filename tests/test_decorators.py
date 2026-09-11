"""Tests des décorateurs require_authentification et admin_required.

Ces décorateurs sont testés sur une application minimale, indépendante des
routes métier : on vérifie l'authentification (qui es-tu ?) et l'autorisation
(as-tu le droit ?) sans passer par les produits.
"""
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from flask import Flask, g, jsonify

import app as app_module
from app import admin_required, require_authentification
from models import UserRole


@pytest.fixture
def probe_app():
    probe = Flask(__name__)

    @probe.get("/protected")
    @require_authentification
    def protected():
        return jsonify({"user_id": g.user_id, "role": g.user_role}), 200

    @probe.get("/admin-only")
    @admin_required
    def admin_only():
        return jsonify({"ok": True}), 200

    return probe


@pytest.fixture
def probe_client(probe_app):
    return probe_app.test_client()


USER_ID = "11111111-1111-1111-1111-111111111111"


def make_token(role, sub=USER_ID, expires_in=timedelta(hours=1), secret=None):
    return jwt.encode(
        {
            "exp": datetime.now(timezone.utc) + expires_in,
            "role": role,
            "sub": sub,
        },
        secret or app_module.JWT_SECRET,
        algorithm="HS256",
    )


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


## require_authentification : l'identité
def test_require_authentification_accepte_un_token_valide(probe_client):
    response = probe_client.get(
        "/protected", headers=bearer(make_token(UserRole.ADMIN))
    )

    assert response.status_code == 200
    assert response.get_json() == {"user_id": USER_ID, "role": "admin"}


def test_require_authentification_accepte_aussi_un_client(probe_client):
    """S'authentifier n'est pas être admin : un client passe ce décorateur."""
    response = probe_client.get(
        "/protected", headers=bearer(make_token(UserRole.CLIENT))
    )

    assert response.status_code == 200
    assert response.get_json()["role"] == "client"


def test_require_authentification_refuse_sans_header(probe_client):
    response = probe_client.get("/protected")

    assert response.status_code == 401


def test_require_authentification_refuse_un_header_sans_bearer(probe_client):
    response = probe_client.get(
        "/protected", headers={"Authorization": make_token(UserRole.ADMIN)}
    )

    assert response.status_code == 401


def test_require_authentification_refuse_un_token_illisible(probe_client):
    response = probe_client.get("/protected", headers=bearer("pas-un-jwt"))

    assert response.status_code == 401


def test_require_authentification_refuse_un_token_expire(probe_client):
    expired = make_token(UserRole.ADMIN, expires_in=timedelta(hours=-1))

    response = probe_client.get("/protected", headers=bearer(expired))

    assert response.status_code == 401


def test_require_authentification_refuse_un_autre_secret(probe_client):
    """Un jeton forgé avec une autre clé ne doit pas être accepté."""
    forged = make_token(UserRole.ADMIN, secret="mauvais-secret")

    response = probe_client.get("/protected", headers=bearer(forged))

    assert response.status_code == 401


## admin_required : l'autorisation
def test_admin_required_autorise_un_admin(probe_client):
    response = probe_client.get(
        "/admin-only", headers=bearer(make_token(UserRole.ADMIN))
    )

    assert response.status_code == 200
    assert response.get_json() == {"ok": True}


def test_admin_required_refuse_un_client(probe_client):
    """Le coeur du test de rôle : authentifié mais pas admin => 403."""
    response = probe_client.get(
        "/admin-only", headers=bearer(make_token(UserRole.CLIENT))
    )

    assert response.status_code == 403
    assert "administrateur" in response.get_json()["error"]


def test_admin_required_refuse_un_role_inconnu(probe_client):
    response = probe_client.get(
        "/admin-only", headers=bearer(make_token("super-utilisateur"))
    )

    assert response.status_code == 403


def test_admin_required_refuse_un_anonyme(probe_client):
    """401 (pas 403) : l'authentification est vérifiée avant le rôle."""
    response = probe_client.get("/admin-only")

    assert response.status_code == 401
