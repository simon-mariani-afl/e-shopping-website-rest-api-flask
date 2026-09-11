"""Tests des routes produits.

Chaque route protégée est testée trois fois : admin (autorisé), client
(interdit, 403) et anonyme (non authentifié, 401).
"""
import uuid

from models import Product

ID_INEXISTANT = uuid.uuid4()

CORPS_VALIDE = {
    "name": "Clavier mécanique sans fil",
    "category": "Périphériques",
    "description": "Switches rouges, Bluetooth",
    "price": 109.99,
    "stock": 12,
}


## list_products : lecture publique
def test_list_products_renvoie_une_liste_vide(client):
    response = client.get("/api/produits")

    assert response.status_code == 200
    assert response.get_json() == {"products": []}


def test_list_products_renvoie_les_produits(client, product):
    response = client.get("/api/produits")

    assert response.status_code == 200
    produits = response.get_json()["products"]
    assert [p["name"] for p in produits] == ["Clavier mécanique"]


def test_list_products_est_accessible_sans_token(client, product):
    """La consultation du catalogue ne demande aucune authentification."""
    assert client.get("/api/produits").status_code == 200


## get_product
def test_get_product_renvoie_le_produit(client, product):
    response = client.get(f"/api/produits/{product.id}")

    assert response.status_code == 200
    assert response.get_json()["product"]["name"] == "Clavier mécanique"


def test_get_product_renvoie_404_si_inconnu(client):
    response = client.get(f"/api/produits/{ID_INEXISTANT}")

    assert response.status_code == 404
    assert "existe pas" in response.get_json()["error"]


def test_get_product_renvoie_404_si_id_mal_forme(client):
    """Le convertisseur <uuid:id> rejette ce qui n'est pas un UUID."""
    assert client.get("/api/produits/abc").status_code == 404


## create_product
def test_create_product_par_un_admin(client, admin_headers, flask_app):
    response = client.post("/api/produits", headers=admin_headers, json=CORPS_VALIDE)

    assert response.status_code == 201
    corps = response.get_json()
    assert corps["id"]
    assert corps["name"] == CORPS_VALIDE["name"]
    assert corps["price"] == 109.99
    assert corps["stock"] == 12
    assert Product.query.count() == 1


def test_create_product_refuse_un_client(client, customer_headers, flask_app):
    """Rôle client : authentifié mais pas autorisé à écrire le catalogue."""
    response = client.post("/api/produits", headers=customer_headers, json=CORPS_VALIDE)

    assert response.status_code == 403
    assert Product.query.count() == 0


def test_create_product_refuse_un_anonyme(client, flask_app):
    response = client.post("/api/produits", json=CORPS_VALIDE)

    assert response.status_code == 401
    assert Product.query.count() == 0


def test_create_product_refuse_un_corps_incomplet(client, admin_headers, flask_app):
    response = client.post(
        "/api/produits", headers=admin_headers, json={"name": "Sans catégorie"}
    )

    assert response.status_code == 400
    assert Product.query.count() == 0


## modify_product
def test_modify_product_par_un_admin(client, admin_headers, product):
    response = client.put(
        f"/api/produits/{product.id}", headers=admin_headers, json=CORPS_VALIDE
    )

    assert response.status_code == 200
    modifie = response.get_json()["product"]
    assert modifie["name"] == CORPS_VALIDE["name"]
    assert modifie["price"] == 109.99
    assert modifie["stock"] == 12


def test_modify_product_conserve_lidentifiant(client, admin_headers, product):
    id_avant = str(product.id)

    response = client.put(
        f"/api/produits/{id_avant}", headers=admin_headers, json=CORPS_VALIDE
    )

    assert response.get_json()["product"]["id"] == id_avant


def test_modify_product_enregistre_en_base(client, admin_headers, product):
    client.put(f"/api/produits/{product.id}", headers=admin_headers, json=CORPS_VALIDE)

    relu = client.get(f"/api/produits/{product.id}").get_json()["product"]
    assert relu["name"] == CORPS_VALIDE["name"]


def test_modify_product_remplace_les_champs_absents(client, admin_headers, product):
    """PUT = remplacement complet : un champ optionnel omis est vidé."""
    response = client.put(
        f"/api/produits/{product.id}",
        headers=admin_headers,
        json={"name": "Clavier nu", "category": "Périphériques", "price": 10.0},
    )

    modifie = response.get_json()["product"]
    assert modifie["description"] is None
    assert modifie["stock"] == 0


def test_modify_product_renvoie_404_si_inconnu(client, admin_headers):
    response = client.put(
        f"/api/produits/{ID_INEXISTANT}", headers=admin_headers, json=CORPS_VALIDE
    )

    assert response.status_code == 404


def test_modify_product_refuse_un_corps_incomplet(client, admin_headers, product):
    response = client.put(
        f"/api/produits/{product.id}",
        headers=admin_headers,
        json={"name": "Clavier sans catégorie", "price": 50.0},
    )

    assert response.status_code == 400


def test_modify_product_refuse_un_client(client, customer_headers, product):
    response = client.put(
        f"/api/produits/{product.id}", headers=customer_headers, json=CORPS_VALIDE
    )

    assert response.status_code == 403
    assert product.name == "Clavier mécanique"


def test_modify_product_refuse_un_anonyme(client, product):
    response = client.put(f"/api/produits/{product.id}", json=CORPS_VALIDE)

    assert response.status_code == 401
    assert product.name == "Clavier mécanique"


## delete_product
def test_delete_product_par_un_admin(client, admin_headers, product, flask_app):
    response = client.delete(f"/api/produits/{product.id}", headers=admin_headers)

    assert response.status_code in (200, 204)
    assert Product.query.count() == 0


def test_delete_product_rend_le_produit_introuvable(client, admin_headers, product):
    identifiant = str(product.id)

    client.delete(f"/api/produits/{identifiant}", headers=admin_headers)

    assert client.get(f"/api/produits/{identifiant}").status_code == 404


def test_delete_product_deux_fois_renvoie_404(client, admin_headers, product):
    identifiant = str(product.id)
    client.delete(f"/api/produits/{identifiant}", headers=admin_headers)

    response = client.delete(f"/api/produits/{identifiant}", headers=admin_headers)

    assert response.status_code == 404


def test_delete_product_renvoie_404_si_inconnu(client, admin_headers):
    response = client.delete(f"/api/produits/{ID_INEXISTANT}", headers=admin_headers)

    assert response.status_code == 404


def test_delete_product_refuse_un_client(client, customer_headers, product, flask_app):
    """Rôle client : ne doit pas pouvoir supprimer un produit."""
    response = client.delete(f"/api/produits/{product.id}", headers=customer_headers)

    assert response.status_code == 403
    assert Product.query.count() == 1


def test_delete_product_refuse_un_anonyme(client, product, flask_app):
    response = client.delete(f"/api/produits/{product.id}")

    assert response.status_code == 401
    assert Product.query.count() == 1
