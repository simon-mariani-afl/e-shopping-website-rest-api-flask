# Tests des routes /api/auth/register et /api/auth/login

from app import decode_token
from models import Utilisateur, UserRole
from conftest import CLIENT_EMAIL, CLIENT_PASSWORD


## register
def test_register_cree_un_utilisateur(client, flask_app):
    response = client.post(
        "/api/auth/register",
        json={"email": "nouveau@digimarket.com", "nom": "Nouveau", "password": "Motdepasse1!"},
    )

    assert response.status_code == 201
    corps = response.get_json()
    assert corps["email"] == "nouveau@digimarket.com"
    assert corps["id"]
    assert Utilisateur.query.filter_by(email="nouveau@digimarket.com").first() is not None


def test_register_attribue_le_role_client(client):
    """Un compte créé publiquement doit être simple client"""
    response = client.post(
        "/api/auth/register",
        json={"email": "nouveau@digimarket.com", "nom": "Nouveau", "password": "Motdepasse1!"},
    )

    assert response.get_json()["role"] == "client"


def test_register_ignore_un_role_admin_demande_par_le_client(client, flask_app):
    """Escalade de privilèges : le champ role du corps ne doit pas être lu."""
    client.post(
        "/api/auth/register",
        json={
            "email": "malin@digimarket.com",
            "nom": "Malin",
            "password": "Motdepasse1!",
            "role": "admin",
        },
    )

    cree = Utilisateur.query.filter_by(email="malin@digimarket.com").first()
    assert cree.role == UserRole.CLIENT


def test_register_ne_renvoie_pas_le_mot_de_passe(client):
    response = client.post(
        "/api/auth/register",
        json={"email": "nouveau@digimarket.com", "nom": "Nouveau", "password": "Motdepasse1!"},
    )

    assert "password" not in response.get_json()
    assert "mot_de_passe" not in response.get_json()


def test_register_refuse_un_email_deja_pris(client, customer):
    response = client.post(
        "/api/auth/register",
        json={"email": CLIENT_EMAIL, "nom": "Autre", "password": "AutreMotdepasse1!"},
    )

    assert response.status_code == 400
    assert "existant" in response.get_json()["error"]


def test_register_refuse_un_corps_incomplet(client):
    response = client.post("/api/auth/register", json={"email": "a@b.com"})

    assert response.status_code == 400


## login
def test_login_renvoie_un_token_utilisable(client, customer):
    response = client.post(
        "/api/auth/login",
        json={"email": CLIENT_EMAIL, "password": CLIENT_PASSWORD},
    )

    assert response.status_code == 200
    corps = response.get_json()
    payload = decode_token(corps["token"])
    assert payload["sub"] == str(customer.id)
    assert payload["role"] == "client"


def test_login_dun_admin_porte_le_role_admin(client, admin):
    """Le rôle voyage dans le jeton : c'est lui qui ouvrira les routes admin."""
    response = client.post(
        "/api/auth/login",
        json={"email": admin.email, "password": "Admin1234!"},
    )

    assert response.status_code == 200
    assert decode_token(response.get_json()["token"])["role"] == "admin"


def test_login_renvoie_aussi_lutilisateur(client, customer):
    response = client.post(
        "/api/auth/login",
        json={"email": CLIENT_EMAIL, "password": CLIENT_PASSWORD},
    )

    assert response.get_json()["user"]["email"] == CLIENT_EMAIL


def test_login_refuse_un_mauvais_mot_de_passe(client, customer):
    response = client.post(
        "/api/auth/login",
        json={"email": CLIENT_EMAIL, "password": "mauvais"},
    )

    assert response.status_code == 400
    assert "mot de passe" in response.get_json()["error"]


def test_login_refuse_un_utilisateur_inconnu(client):
    response = client.post(
        "/api/auth/login",
        json={"email": "fantome@digimarket.com", "password": "Motdepasse1!"},
    )

    assert response.status_code == 400


def test_login_refuse_un_corps_incomplet(client):
    response = client.post("/api/auth/login", json={"email": CLIENT_EMAIL})

    assert response.status_code == 400
