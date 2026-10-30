"""Tests de generate_token et decode_token."""
from datetime import datetime, timedelta, timezone

import jwt

import app as app_module
from app import decode_token, generate_token
from models import Utilisateur, UserRole


def _user(role=UserRole.CLIENT):
    """Un utilisateur non persisté : l'id est posé à la main, car la valeur
    par défaut de la colonne ne serait appliquée qu'à l'insertion en base."""
    user = Utilisateur(id="22222", email="jeton@digimarket.fr", role=role)
    user.set_password("Motdepasse1!")
    return user


def _payload(token):
    return jwt.decode(token, app_module.JWT_SECRET, algorithms=["HS256"])


## generate_token
def test_generate_token_contient_identifiant_et_role():
    user = _user(UserRole.ADMIN)

    payload = _payload(generate_token(user))

    assert payload["sub"] == str(user.id)
    assert payload["role"] == "admin"


def test_generate_token_conserve_le_role_client():
    payload = _payload(generate_token(_user(UserRole.CLIENT)))

    assert payload["role"] == "client"


def test_generate_token_expire_dans_une_heure():
    payload = _payload(generate_token(_user()))

    expiration = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    marge = abs(expiration - (datetime.now(timezone.utc) + timedelta(hours=1)))
    assert marge < timedelta(minutes=1)


def test_generate_token_est_signe_avec_le_secret_de_lapplication():
    token = generate_token(_user())

    try:
        jwt.decode(token, "un-autre-secret", algorithms=["HS256"])
    except jwt.InvalidSignatureError:
        pass
    else:
        raise AssertionError("le jeton ne devrait pas être décodable avec un autre secret")


## decode_token
def test_decode_token_relit_un_token_valide():
    user = _user(UserRole.ADMIN)

    payload = decode_token(generate_token(user))

    assert payload["sub"] == str(user.id)
    assert payload["role"] == "admin"


def test_decode_token_renvoie_none_si_illisible():
    assert decode_token("pas-un-jwt") is None


def test_decode_token_renvoie_none_si_expire():
    """decode_token avale les exceptions de PyJWT et renvoie None."""
    expired = jwt.encode(
        {
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
            "role": UserRole.ADMIN,
            "sub": "11111111-1111-1111-1111-111111111111",
        },
        app_module.JWT_SECRET,
        algorithm="HS256",
    )

    assert decode_token(expired) is None


def test_decode_token_renvoie_none_si_mauvaise_signature():
    forged = jwt.encode({"sub": "x", "role": "admin"}, "mauvais-secret", algorithm="HS256")

    assert decode_token(forged) is None
