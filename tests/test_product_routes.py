#Tests des routes produits

from models import Produit

ID_INEXISTANT = "11111"

CORPS_VALIDE = {
    "nom": "Clavier mécanique sans fil",
    "categorie": "Périphériques",
    "description": "Switches rouges, Bluetooth",
    "prix": 109.99,
    "quantite_stock": 12,
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
    assert [p["nom"] for p in produits] == ["Clavier"]


def test_list_products_est_accessible_sans_token(client, product):
    """La consultation du catalogue ne demande aucune authentification."""
    assert client.get("/api/produits").status_code == 200


## get_product
def test_get_product_renvoie_le_produit(client, product):
    response = client.get(f"/api/produits/{product.id}")

    assert response.status_code == 200
    assert response.get_json()["product"]["nom"] == "Clavier"


def test_get_product_renvoie_404_si_inconnu(client):
    response = client.get(f"/api/produits/{ID_INEXISTANT}")

    assert response.status_code == 404
    assert "existe pas" in response.get_json()["error"]


def test_get_product_renvoie_404_si_id_mal_forme(client):
    """Le convertisseur rejette ce qui n'est pas un Integer."""
    assert client.get("/api/produits/abc").status_code == 404


## create_product
def test_create_product_par_un_admin(client, admin_headers, flask_app):
    response = client.post("/api/produits", headers=admin_headers, json=CORPS_VALIDE)

    assert response.status_code == 201
    corps = response.get_json()
    assert corps["id"]
    assert corps["nom"] == CORPS_VALIDE["nom"]
    assert corps["prix"] == 109.99
    assert corps["quantite_stock"] == 12
    assert Produit.query.count() == 1


def test_create_product_refuse_un_client(client, customer_headers, flask_app):
    """Rôle client : authentifié mais pas autorisé à écrire le catalogue."""
    response = client.post("/api/produits", headers=customer_headers, json=CORPS_VALIDE)

    assert response.status_code == 403
    assert Produit.query.count() == 0


def test_create_product_refuse_un_anonyme(client, flask_app):
    response = client.post("/api/produits", json=CORPS_VALIDE)

    assert response.status_code == 401
    assert Produit.query.count() == 0


def test_create_product_refuse_un_corps_incomplet(client, admin_headers, flask_app):
    response = client.post(
        "/api/produits", headers=admin_headers, json={"nom": "Sans catégorie"}
    )

    assert response.status_code == 400
    assert Produit.query.count() == 0


## modify_product
def test_modify_product_par_un_admin(client, admin_headers, product):
    response = client.put(
        f"/api/produits/{product.id}", headers=admin_headers, json=CORPS_VALIDE
    )

    assert response.status_code == 200
    modifie = response.get_json()["product"]
    assert modifie["nom"] == CORPS_VALIDE["nom"]
    assert modifie["prix"] == 109.99
    assert modifie["quantite_stock"] == 12


def test_modify_product_conserve_lidentifiant(client, admin_headers, product):
    id_avant = product.id

    response = client.put(
        f"/api/produits/{id_avant}", headers=admin_headers, json=CORPS_VALIDE
    )

    assert response.get_json()["product"]["id"] == id_avant


def test_modify_product_enregistre_en_base(client, admin_headers, product):
    client.put(f"/api/produits/{product.id}", headers=admin_headers, json=CORPS_VALIDE)

    relu = client.get(f"/api/produits/{product.id}").get_json()["product"]
    assert relu["nom"] == CORPS_VALIDE["nom"]


def test_modify_product_remplace_les_champs_absents(client, admin_headers, product):
    """PUT = remplacement complet : un champ optionnel omis est vidé."""
    response = client.put(
        f"/api/produits/{product.id}",
        headers=admin_headers,
        json={"nom": "Clavier nu", "categorie": "Périphériques", "prix": 10.0},
    )

    modifie = response.get_json()["product"]
    assert modifie["description"] is None
    assert modifie["quantite_stock"] == 0


def test_modify_product_renvoie_404_si_inconnu(client, admin_headers):
    response = client.put(
        f"/api/produits/{ID_INEXISTANT}", headers=admin_headers, json=CORPS_VALIDE
    )

    assert response.status_code == 404


def test_modify_product_refuse_un_corps_incomplet(client, admin_headers, product):
    response = client.put(
        f"/api/produits/{product.id}",
        headers=admin_headers,
        json={"nom": "Clavier sans catégorie", "prix": 50.0},
    )

    assert response.status_code == 400


def test_modify_product_refuse_un_client(client, customer_headers, product):
    response = client.put(
        f"/api/produits/{product.id}", headers=customer_headers, json=CORPS_VALIDE
    )

    assert response.status_code == 403
    assert product.nom == "Clavier"


def test_modify_product_refuse_un_anonyme(client, product):
    response = client.put(f"/api/produits/{product.id}", json=CORPS_VALIDE)

    assert response.status_code == 401
    assert product.nom == "Clavier"


## delete_product
def test_delete_product_par_un_admin(client, admin_headers, product, flask_app):
    response = client.delete(f"/api/produits/{product.id}", headers=admin_headers)

    assert response.status_code in (200, 204)
    assert Produit.query.count() == 0


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
    assert Produit.query.count() == 1


def test_delete_product_refuse_un_anonyme(client, product, flask_app):
    response = client.delete(f"/api/produits/{product.id}")

    assert response.status_code == 401
    assert Produit.query.count() == 1
