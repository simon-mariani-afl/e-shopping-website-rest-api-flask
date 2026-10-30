"""Tests des validateurs de libs/.

Ces fonctions ne renvoient rien : elles coupent la requête avec un abort(400).
On vérifie donc l'exception HTTP levée, et son corps JSON.
"""
import pytest
from werkzeug.exceptions import HTTPException

from libs.check_auth_required_fields import check_auth_required_fields
from libs.check_order_required_fields import check_order_required_fields
from libs.check_product_required_fields import check_product_required_fields


def _abort_status_and_error(fonction, body):
    """Appelle le validateur et renvoie (code, message d'erreur) de l'abort."""
    with pytest.raises(HTTPException) as erreur:
        fonction(body)

    response = erreur.value.get_response()
    return response.status_code, response.get_json()["error"]


## check_auth_required_fields
def test_check_auth_accepte_un_corps_complet(flask_app):
    assert check_auth_required_fields({"email": "a@b.fr", "password": "secret"}) is None


def test_check_auth_accepte_les_champs_supplementaires(flask_app):
    body = {"email": "a@b.fr", "password": "secret", "surnom": "sim"}

    assert check_auth_required_fields(body) is None


@pytest.mark.parametrize(
    "body",
    [
        pytest.param({"password": "secret"}, id="email-manquant"),
        pytest.param({"email": "a@b.fr"}, id="password-manquant"),
        pytest.param({"email": "", "password": "secret"}, id="email-vide"),
        pytest.param({"email": "a@b.fr", "password": ""}, id="password-vide"),
        pytest.param({}, id="corps-vide"),
        pytest.param(None, id="pas-de-corps"),
    ],
)
def test_check_auth_refuse_un_corps_incomplet(flask_app, body):
    status, error = _abort_status_and_error(check_auth_required_fields, body)

    assert status == 400
    assert "mot de passe" in error


## check_product_required_fields
def test_check_produit_accepte_un_corps_complet(flask_app):
    body = {"nom": "Clavier", "categorie": "Périphériques", "prix": 89.99}

    assert check_product_required_fields(body) is None


def test_check_produit_naccepte_pas_dexiger_stock_et_description(flask_app):
    """quantite_stock et description sont optionnels : leur absence ne bloque pas."""
    body = {"nom": "Clavier", "categorie": "Périphériques", "prix": 89.99}

    assert check_product_required_fields(body) is None
    assert "quantite_stock" not in body


@pytest.mark.parametrize(
    "body",
    [
        pytest.param({"categorie": "Périphériques", "prix": 89.99}, id="nom-manquant"),
        pytest.param({"nom": "Clavier", "prix": 89.99}, id="categorie-manquante"),
        pytest.param({"nom": "Clavier", "categorie": "Périphériques"}, id="prix-manquant"),
        pytest.param({"nom": "", "categorie": "Périphériques", "prix": 89.99}, id="nom-vide"),
        pytest.param({}, id="corps-vide"),
        pytest.param(None, id="pas-de-corps"),
    ],
)
def test_check_produit_refuse_un_corps_incomplet(flask_app, body):
    status, error = _abort_status_and_error(check_product_required_fields, body)

    assert status == 400
    assert "produit" in error


def test_check_produit_refuse_un_prix_a_zero(flask_app):
    """Effet de bord du test `not body.get(field)` : 0 est considéré manquant.

    Ce test documente le comportement actuel. Si un produit gratuit doit être
    autorisé, il faudra tester la présence de la clé plutôt que sa valeur.
    """
    status, _ = _abort_status_and_error(
        check_product_required_fields,
        {"nom": "Goodie", "categorie": "Divers", "prix": 0},
    )

    assert status == 400


## check_order_required_fields
COMMANDE_VALIDE = {
    "adresse_livraison": "12 rue de la Paix, Paris",
    "lignecommandes": [{"produit_id": 1, "quantite": 2}],
}


def test_check_commande_accepte_un_corps_complet(flask_app):
    assert check_order_required_fields(COMMANDE_VALIDE) is None


@pytest.mark.parametrize(
    "body",
    [
        pytest.param(None, id="pas-de-corps"),
        pytest.param([], id="corps-pas-un-objet"),
        pytest.param({}, id="corps-vide"),
        pytest.param({**COMMANDE_VALIDE, "adresse_livraison": ""}, id="adresse-vide"),
        pytest.param({**COMMANDE_VALIDE, "adresse_livraison": 5}, id="adresse-pas-une-chaine"),
        pytest.param({"adresse_livraison": "x"}, id="lignes-manquantes"),
        pytest.param({**COMMANDE_VALIDE, "lignecommandes": []}, id="lignes-vides"),
        pytest.param({**COMMANDE_VALIDE, "lignecommandes": "x"}, id="lignes-pas-une-liste"),
        pytest.param({**COMMANDE_VALIDE, "lignecommandes": [3]}, id="ligne-pas-un-objet"),
        pytest.param({**COMMANDE_VALIDE, "lignecommandes": [{"quantite": 1}]}, id="produit_id-manquant"),
        pytest.param({**COMMANDE_VALIDE, "lignecommandes": [{"produit_id": 1}]}, id="quantite-manquante"),
        pytest.param({**COMMANDE_VALIDE, "lignecommandes": [{"produit_id": 1, "quantite": -2}]}, id="quantite-negative"),
        pytest.param({**COMMANDE_VALIDE, "lignecommandes": [{"produit_id": 1, "quantite": "abc"}]}, id="quantite-texte"),
        pytest.param({**COMMANDE_VALIDE, "lignecommandes": [{"produit_id": 1, "quantite": 1.5}]}, id="quantite-decimale"),
        pytest.param({**COMMANDE_VALIDE, "lignecommandes": [{"produit_id": 1, "quantite": True}]}, id="quantite-booleenne"),
    ],
)
def test_check_commande_refuse_un_corps_invalide(flask_app, body):
    status, error = _abort_status_and_error(check_order_required_fields, body)

    assert status == 400
    assert "commande" in error
