import requests
import json
import uuid

BASE_URL = "http://127.0.0.1:5000"

def print_response(response):
    print(f"Status: {response.status_code}")
    print("Response:", json.dumps(response.json(), indent=2))

response = requests.post(
    f"{BASE_URL}/api/auth/register",
    json={"email": "sim.13mr@gmail.com", "password": "motdepasse"}
)

response = requests.post(
    f"{BASE_URL}/api/auth/login",
    json={"email": "sim.13mr@gmail.com", "password": "motdepasse"}
)

print_response(response)


## Création d'un produit par un administrateur
print("\n--- Connexion administrateur ---")
admin_login = requests.post(
    f"{BASE_URL}/api/auth/login",
    json={"email": "admin@digimarket.fr", "password": "Admin1234!"}
)
print_response(admin_login)

admin_token = admin_login.json().get("token")

print("\n--- Création du produit (admin) ---")
create_admin = requests.post(
    f"{BASE_URL}/api/produits",
    headers={"Authorization": f"Bearer {admin_token}"}, # IL FAUT METTRE LE TOKEN ICI DANS LE HEADER
    json={
        "name": "Clavier mécanique",
        "category": "Périphériques",
        "description": "Clavier switches rouges, rétroéclairé",
        "price": 89.99,
        "stock": 25
    }
)
print_response(create_admin)

# On attend 201 et un produit renvoyé avec un id
assert create_admin.status_code == 201, f"attendu 201, reçu {create_admin.status_code}"
created = create_admin.json()
assert created.get("id"), "le produit créé devrait avoir un id"
assert created["name"] == "Clavier mécanique"
assert created["price"] == 89.99
assert created["stock"] == 25
print("OK : l'administrateur peut créer un produit.")

# Le produit doit maintenant apparaître dans la liste
print("\n--- Vérification dans la liste des produits ---")
listing = requests.get(f"{BASE_URL}/api/produits")
print(f"Status: {listing.status_code}")
if listing.status_code == 200:
    names = [p["name"] for p in listing.json().get("products", [])]
    assert "Clavier mécanique" in names, "le produit créé est absent de la liste"
    print("OK : le produit est bien présent dans la liste.")
else:
    print("La liste des produits n'a pas pu être vérifiée.")


## Contre-épreuves : un client ne doit pas pouvoir créer de produit
print("\n--- Création du produit par un client ---")
client_token = response.json().get("token")
if client_token:
    client_create = requests.post(
        f"{BASE_URL}/api/produits",
        headers={"Authorization": f"Bearer {client_token}"},
        json={"name": "Produit pirate", "category": "Divers", "price": 1.0}
    )
    print(f"Status: {client_create.status_code}")
    assert client_create.status_code == 403, f"attendu 403, reçu {client_create.status_code}"
    print("OK : un client est bien refusé (403).")
else:
    print("Pas de token client disponible, test ignoré.")

## Modification du produit (PUT)
product_id = created["id"]
product_url = f"{BASE_URL}/api/produits/{product_id}"

print("\n--- Modification du produit (admin) ---")
update_admin = requests.put(
    product_url,
    headers={"Authorization": f"Bearer {admin_token}"},
    json={
        "name": "Clavier mécanique sans fil",
        "category": "Périphériques",
        "description": "Clavier switches rouges, Bluetooth",
        "price": 109.99,
        "stock": 12
    }
)
print_response(update_admin)

assert update_admin.status_code == 200, f"attendu 200, reçu {update_admin.status_code}"
updated = update_admin.json()["product"]
assert updated["id"] == product_id, "l'id ne doit pas changer lors d'une modification"
assert updated["name"] == "Clavier mécanique sans fil"
assert updated["price"] == 109.99
assert updated["stock"] == 12
print("OK : l'administrateur peut modifier un produit.")

# La modification doit être persistée : on relit le produit
print("\n--- Relecture du produit modifié ---")
reread = requests.get(product_url)
print_response(reread)
assert reread.status_code == 200, f"attendu 200, reçu {reread.status_code}"
assert reread.json()["product"]["name"] == "Clavier mécanique sans fil"
print("OK : la modification est bien enregistrée en base.")

# PUT = remplacement complet : un champ obligatoire manquant doit être refusé
print("\n--- Modification avec un champ obligatoire manquant ---")
update_incomplete = requests.put(
    product_url,
    headers={"Authorization": f"Bearer {admin_token}"},
    json={"name": "Clavier sans catégorie", "price": 50.0}
)
print(f"Status: {update_incomplete.status_code}")
assert update_incomplete.status_code == 400, f"attendu 400, reçu {update_incomplete.status_code}"
print("OK : un corps incomplet est bien refusé (400).")

# Un produit inexistant doit renvoyer 404
print("\n--- Modification d'un produit inexistant ---")
unknown_url = f"{BASE_URL}/api/produits/{uuid.uuid4()}"
update_unknown = requests.put(
    unknown_url,
    headers={"Authorization": f"Bearer {admin_token}"},
    json={"name": "Fantôme", "category": "Divers", "price": 1.0}
)
print(f"Status: {update_unknown.status_code}")
assert update_unknown.status_code == 404, f"attendu 404, reçu {update_unknown.status_code}"
print("OK : un produit inexistant renvoie bien 404.")

## Contre-épreuves sur la modification
if client_token:
    print("\n--- Modification par un client ---")
    update_client = requests.put(
        product_url,
        headers={"Authorization": f"Bearer {client_token}"},
        json={"name": "Pirate", "category": "Divers", "price": 1.0}
    )
    print(f"Status: {update_client.status_code}")
    assert update_client.status_code == 403, f"attendu 403, reçu {update_client.status_code}"
    print("OK : un client ne peut pas modifier un produit (403).")
else:
    print("Pas de token client disponible, test ignoré.")


## Suppression du produit (DELETE)
## Les contre-épreuves passent d'abord : une fois supprimé, le produit n'existe plus.

if client_token:
    print("\n--- Suppression par un client ---")
    delete_client = requests.delete(
        product_url,
        headers={"Authorization": f"Bearer {client_token}"}
    )
    print(f"Status: {delete_client.status_code}")
    assert delete_client.status_code == 403, f"attendu 403, reçu {delete_client.status_code}"
    print("OK : un client ne peut pas supprimer un produit (403).")
else:
    print("Pas de token client disponible, test ignoré.")

print("\n--- Suppression du produit (admin) ---")
delete_admin = requests.delete(
    product_url,
    headers={"Authorization": f"Bearer {admin_token}"}
)
# Une réponse 204 n'a pas de corps : on n'appelle pas print_response ici
print(f"Status: {delete_admin.status_code}")
assert delete_admin.status_code in (200, 204), f"attendu 200 ou 204, reçu {delete_admin.status_code}"
print("OK : l'administrateur peut supprimer un produit.")

# Le produit ne doit plus être accessible ni présent dans la liste
print("\n--- Vérification de la suppression ---")
after_delete = requests.get(product_url)
print(f"Status: {after_delete.status_code}")
assert after_delete.status_code == 404, f"attendu 404, reçu {after_delete.status_code}"

listing_after = requests.get(f"{BASE_URL}/api/produits")
ids_after = [p["id"] for p in listing_after.json().get("products", [])]
assert product_id not in ids_after, "le produit supprimé est encore dans la liste"
print("OK : le produit est bien supprimé.")

# Supprimer deux fois le même produit doit renvoyer 404
print("\n--- Seconde suppression du même produit ---")
delete_again = requests.delete(
    product_url,
    headers={"Authorization": f"Bearer {admin_token}"}
)
print(f"Status: {delete_again.status_code}")
assert delete_again.status_code == 404, f"attendu 404, reçu {delete_again.status_code}"
print("OK : supprimer un produit déjà supprimé renvoie bien 404.")
