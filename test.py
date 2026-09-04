import requests
import json

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


## Contre-épreuves : un client et un anonyme ne doivent pas pouvoir créer un produit
print("\n--- Création du produit sans token ---")
anon = requests.post(
    f"{BASE_URL}/api/produits",
    json={"name": "Produit pirate", "category": "Divers", "price": 1.0}
)
print(f"Status: {anon.status_code}")
assert anon.status_code == 401, f"attendu 401, reçu {anon.status_code}"
print("OK : un anonyme est bien refusé (401).")

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
