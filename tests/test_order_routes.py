# Tests des routes des commandes

import pytest
import app as app_module
from models import Commande, LigneCommande, OrderStatus, Produit, Utilisateur, UserRole, db

ID_INEXISTANT = "11111"


@pytest.fixture
def order(customer, product):
    """Une commande du client : 2 x 100.0 (le produit de la fixture)."""
    commande = Commande(utilisateur_id=customer.id, adresse_livraison="12 rue de la Paix, Paris")
    commande.lignecommandes.append(
        LigneCommande(produit_id=product.id, quantite=2, prix_unitaire=product.prix)
    )
    db.session.add(commande)
    db.session.commit()
    return commande


@pytest.fixture
def other_headers(flask_app):
    """Un second client, étranger à la commande."""
    other = Utilisateur(email="autre@digimarket.com", nom="Autre", role=UserRole.CLIENT)
    other.set_password("Autre1234!")
    db.session.add(other)
    db.session.commit()
    return {"Authorization": f"Bearer {app_module.generate_token(other)}"}


## get_order
def test_get_order_par_le_proprietaire(client, order, customer_headers):
    response = client.get(f"/api/commandes/{order.id}", headers=customer_headers)

    assert response.status_code == 200
    corps = response.get_json()
    assert corps["id"] == order.id
    assert corps["statut"] == "en_attente"
    assert corps["adresse_livraison"] == "12 rue de la Paix, Paris"
    assert len(corps["détail de la commande"]) == 1


def test_get_order_par_un_admin(client, order, admin_headers):
    assert client.get(f"/api/commandes/{order.id}", headers=admin_headers).status_code == 200


def test_get_order_interdit_a_un_autre_client(client, order, other_headers):
    response = client.get(f"/api/commandes/{order.id}", headers=other_headers)

    assert response.status_code == 403


def test_get_order_renvoie_404_si_inconnue(client, customer_headers):
    response = client.get(f"/api/commandes/{ID_INEXISTANT}", headers=customer_headers)

    assert response.status_code == 404


def test_get_order_sans_token(client, order):
    assert client.get(f"/api/commandes/{order.id}").status_code == 401

def test_update_order_status_par_un_admin(client, order, admin_headers):
    response = client.patch(
        f"/api/commandes/{order.id}", headers=admin_headers, json={"statut": "expediee"}
    )

    assert response.status_code == 200
    assert response.get_json()["statut"] == "expediee"
    assert db.session.get(Commande, order.id).statut == OrderStatus.EXPEDIEE

def test_update_order_status_interdit_a_un_client(client, order, customer_headers):
    response = client.patch(
        f"/api/commandes/{order.id}", headers=customer_headers, json={"statut": "annulee"}
    )

    assert response.status_code == 403
    assert db.session.get(Commande, order.id).statut == OrderStatus.EN_ATTENTE


def test_update_order_status_sans_token(client, order):
    response = client.patch(f"/api/commandes/{order.id}", json={"statut": "validee"})

    assert response.status_code == 401


@pytest.mark.parametrize("corps", [{}, {"statut": "n_importe_quoi"}, {"statut": None}, {"statut": 3}])
def test_update_order_status_refuse_un_statut_invalide(client, order, admin_headers, corps):
    response = client.patch(f"/api/commandes/{order.id}", headers=admin_headers, json=corps)

    assert response.status_code == 400
    assert db.session.get(Commande, order.id).statut == OrderStatus.EN_ATTENTE


def test_update_order_status_renvoie_404_si_inconnue(client, admin_headers):
    response = client.patch(
        f"/api/commandes/{ID_INEXISTANT}", headers=admin_headers, json={"statut": "validee"}
    )

    assert response.status_code == 404

def test_list_order_lines_par_le_proprietaire(client, order, product, customer_headers):
    response = client.get(f"/api/commandes/{order.id}/lignes", headers=customer_headers)

    assert response.status_code == 200
    lignes = response.get_json()["lignes"]
    assert len(lignes) == 1
    assert lignes[0]["produit_id"] == product.id
    assert lignes[0]["quantite"] == 2
    assert lignes[0]["prix_unitaire"] == 100.0


def test_list_order_lines_par_un_admin(client, order, admin_headers):
    assert client.get(f"/api/commandes/{order.id}/lignes", headers=admin_headers).status_code == 200


def test_list_order_lines_interdit_a_un_autre_client(client, order, other_headers):
    assert client.get(f"/api/commandes/{order.id}/lignes", headers=other_headers).status_code == 403


def test_list_order_lines_renvoie_404_si_inconnue(client, customer_headers):
    response = client.get(f"/api/commandes/{ID_INEXISTANT}/lignes", headers=customer_headers)

    assert response.status_code == 404


def test_list_order_lines_sans_token(client, order):
    assert client.get(f"/api/commandes/{order.id}/lignes").status_code == 401


## create_order
def _corps_commande(*lignes):
    return {"adresse_livraison": "12 rue de la Paix, Paris", "lignecommandes": list(lignes)}

def test_create_order_enregistre_la_commande(client, customer, customer_headers, product):
    response = client.post(
        "/api/commandes",
        headers=customer_headers,
        json=_corps_commande({"produit_id": product.id, "quantite": 2}),
    )

    assert response.status_code == 201
    corps = response.get_json()
    assert corps["utilisateur_id"] == customer.id
    assert corps["statut"] == "en_attente"
    assert corps["détail de la commande"][0]["prix_unitaire"] == 100.0

def test_create_order_decremente_le_stock(client, customer_headers, product):
    client.post(
        "/api/commandes",
        headers=customer_headers,
        json=_corps_commande({"produit_id": product.id, "quantite": 5}),
    )

    assert db.session.get(Produit, product.id).quantite_stock == 20

def test_create_order_ignore_un_prix_envoye_par_le_client(client, customer_headers, product):
    response = client.post(
        "/api/commandes",
        headers=customer_headers,
        json=_corps_commande({"produit_id": product.id, "quantite": 1, "prix_unitaire": 0.01}),
    )

    assert response.get_json()["détail de la commande"][0]["prix_unitaire"] == 100.0

def test_create_order_renvoie_404_si_produit_inconnu(client, customer_headers):
    response = client.post(
        "/api/commandes",
        headers=customer_headers,
        json=_corps_commande({"produit_id": int(ID_INEXISTANT), "quantite": 1}),
    )

    assert response.status_code == 404
    assert Commande.query.count() == 0

def test_create_order_refuse_un_stock_insuffisant(client, customer_headers, product):
    response = client.post(
        "/api/commandes",
        headers=customer_headers,
        json=_corps_commande({"produit_id": product.id, "quantite": 26}),
    )

    assert response.status_code == 400
    assert "stock insuffisant" in response.get_json()["error"]
    assert Commande.query.count() == 0

def test_create_order_annule_les_stocks_si_une_ligne_echoue(client, customer_headers, product):
    """La 1re ligne est valide, la 2e échoue : le stock de la 1re ne doit pas bouger."""
    response = client.post(
        "/api/commandes",
        headers=customer_headers,
        json=_corps_commande(
            {"produit_id": product.id, "quantite": 5},
            {"produit_id": int(ID_INEXISTANT), "quantite": 1},
        ),
    )
    db.session.expire_all()

    assert response.status_code == 404
    assert db.session.get(Produit, product.id).quantite_stock == 25

def test_create_order_refuse_un_doublon_depassant_le_stock(client, customer_headers, product):
    """Deux lignes du même produit : leur total est comparé au stock, pas chacune."""
    response = client.post(
        "/api/commandes",
        headers=customer_headers,
        json=_corps_commande(
            {"produit_id": product.id, "quantite": 20},
            {"produit_id": product.id, "quantite": 20},
        ),
    )
    db.session.expire_all()

    assert response.status_code == 400
    assert db.session.get(Produit, product.id).quantite_stock == 25

@pytest.mark.parametrize("corps", [{}, {"adresse_livraison": "x"}, {"adresse_livraison": "x", "lignecommandes": []}])
def test_create_order_refuse_un_corps_invalide(client, customer_headers, corps):
    response = client.post("/api/commandes", headers=customer_headers, json=corps)

    assert response.status_code == 400

def test_create_order_sans_token(client, product):
    response = client.post(
        "/api/commandes", json=_corps_commande({"produit_id": product.id, "quantite": 1})
    )

    assert response.status_code == 401
