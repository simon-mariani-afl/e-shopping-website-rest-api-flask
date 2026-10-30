import requests
import json
import uuid

### TEST FILE
## To start from a clean database you need to delete instance/cart.db before launching the server

BASE_URL = "http://127.0.0.1:5000"

def print_response(response):
    print(f"Status: {response.status_code}")
    print("Response:", json.dumps(response.json(), indent=2, ensure_ascii=False))

def auth(token):
    return {"Authorization": f"Bearer {token}"}


# Sur une base vide, app.py ne crée les produits et l'admin qu'à la 2e requête
# (create_tables se retire de la liste des hooks pendant que Flask la parcourt)
requests.get(f"{BASE_URL}/api/produits")
requests.get(f"{BASE_URL}/api/produits")


## 1) Admin (créé par app.py au premier lancement)
print("Connexion de l'admin :")
response = requests.post(f"{BASE_URL}/api/auth/login", json={"email": "admin@digimarket.com", "password": "Admin1234!"})
print_response(response)
admin_token = response.json()["token"]

## 2) Utilisateur
user = {"email": f"client@example.com", "password": "motdepasse"}

print("\nInscription de l'utilisateur :")
response = requests.post(f"{BASE_URL}/api/auth/register", json={**user, "nom": "Client Test"})
print_response(response)

print("\nConnexion de l'utilisateur :")
response = requests.post(f"{BASE_URL}/api/auth/login", json=user)
print_response(response)
user_token = response.json()["token"]


## 3) Tests de l'admin
print("\nListe des produits par n'importe qui :")
response = requests.get(f"{BASE_URL}/api/produits")
print_response(response)

print("\nCréation d'un produit par l'admin :")
response = requests.post(
    f"{BASE_URL}/api/produits",
    headers=auth(admin_token),
    json={"nom": "Clavier joli", "categorie": "Informatique", "description": "très joli", "prix": 100, "quantite_stock": 25},
)
print_response(response)
product_id = response.json()["id"]

print("\nModification du produit par l'admin :")
response = requests.put(
    f"{BASE_URL}/api/produits/{product_id}",
    headers=auth(admin_token),
    json={"nom": "Clavier sans fil", "categorie": "Informatique", "description": "très très joli", "prix": 120, "quantite_stock": 12},
)
print_response(response)

print("\nListe des produits après modification par n'importe qui :")
response = requests.get(f"{BASE_URL}/api/produits")
print_response(response)

print("\nSuppression du produit par l'admin:")
response = requests.delete(f"{BASE_URL}/api/produits/{product_id}", headers=auth(admin_token))
print_response(response)

print("\nListe des commandes par l'admin :")
response = requests.get(f"{BASE_URL}/api/commandes", headers=auth(admin_token))
print_response(response)

print("\nListe des produits par n'importe qui :")
response = requests.get(f"{BASE_URL}/api/produits")
print_response(response)
first_product_id = response.json()["products"][0]["id"]

print("\nCréation d'une commande par l'utilisateur :")
response = requests.post(
    f"{BASE_URL}/api/commandes",
    headers=auth(user_token),
    json={"adresse_livraison": "3 Avenue du Centre - 78000 - Guyancourt", "lignecommandes": [{"produit_id": first_product_id, "quantite": 2}]},
)
print_response(response)
order_id = response.json()["id"]

print("\nListe des produits après la commande par n'importe qui :")
response = requests.get(f"{BASE_URL}/api/produits")
print_response(response)

print("\nListe des commandes de l'utilisateur :")
response = requests.get(f"{BASE_URL}/api/commandes", headers=auth(user_token))
print_response(response)

print("\nDétail de la commande de l'utilisateur :")
response = requests.get(f"{BASE_URL}/api/commandes/{order_id}", headers=auth(user_token))
print_response(response)

print("\nDétails de la commande de l'utilisateur :")
response = requests.get(f"{BASE_URL}/api/commandes/{order_id}/lignes", headers=auth(user_token))
print_response(response)


## 5) L'admin voit la commande et change son statut
print("\nListe de toutes les commandes par l'admin :")
response = requests.get(f"{BASE_URL}/api/commandes", headers=auth(admin_token))
print_response(response)

print("\nChangement du statut de la commande par l'admin :")
response = requests.patch(f"{BASE_URL}/api/commandes/{order_id}", headers=auth(admin_token), json={"statut": "validee"})
print_response(response)
