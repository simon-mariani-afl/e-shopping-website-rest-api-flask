"""Fixtures partagées par les tests unitaires.

La base de test doit être choisie AVANT l'import de `app` : Flask-SQLAlchemy
construit son moteur au moment du `db.init_app(app)`, qui s'exécute à l'import
du module. `sqlite://` = base en mémoire, donc jamais le cart.db de dev.
"""
import os

os.environ.setdefault("JWT_SECRET", "secret-de-test")
os.environ["DATABASE_URI"] = "sqlite://"

import pytest

import app as app_module
from models import Produit, Utilisateur, UserRole, db

ADMIN_EMAIL = "admin-test@digimarket.fr"
ADMIN_PASSWORD = "Admin1234!"
CLIENT_EMAIL = "client-test@digimarket.fr"
CLIENT_PASSWORD = "Client1234!"


@pytest.fixture
def flask_app():
    """L'application, avec une base vide recréée pour chaque test."""
    application = app_module.app
    application.config.update(TESTING=True)

    # create_tables et add_sample_data sont des hooks before_request qui
    # insèrent des données de démo puis se désinscrivent. On les retire :
    # chaque test doit partir d'une base vide et maîtrisée.
    hooks = application.before_request_funcs.get(None, [])
    application.before_request_funcs[None] = [
        hook for hook in hooks
        if hook.__name__ not in ("create_tables", "add_sample_data")
    ]

    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(flask_app):
    """Client HTTP de test (ne nécessite pas de serveur lancé)."""
    return flask_app.test_client()


def _create_user(email, password, role):
    user = Utilisateur(email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def admin(flask_app):
    return _create_user(ADMIN_EMAIL, ADMIN_PASSWORD, UserRole.ADMIN)


@pytest.fixture
def customer(flask_app):
    """Un utilisateur ordinaire, au rôle CLIENT."""
    return _create_user(CLIENT_EMAIL, CLIENT_PASSWORD, UserRole.CLIENT)


@pytest.fixture
def admin_headers(admin):
    return {"Authorization": f"Bearer {app_module.generate_token(admin)}"}


@pytest.fixture
def customer_headers(customer):
    return {"Authorization": f"Bearer {app_module.generate_token(customer)}"}


@pytest.fixture
def product(flask_app):
    product = Produit(
        nom="Clavier mécanique",
        categorie="Périphériques",
        description="Switches rouges, rétroéclairé",
        prix=89.99,
        quantite_stock=25,
    )
    db.session.add(product)
    db.session.commit()
    return product
