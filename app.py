import jwt
from flask import Flask, request, jsonify, g
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from functools import wraps
import os

from models import Utilisateur, Produit, UserRole, OrderStatus, db, Commande, LigneCommande
from libs.check_auth_required_fields import check_auth_required_fields
from libs.check_order_status_field import check_order_status_field
from libs.check_product_required_fields import check_product_required_fields
from libs.check_order_required_fields import check_order_required_fields

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")

app = Flask(__name__)

# Configuration de la base de données
# Surchargeable par DATABASE_URI pour que les tests utilisent une base jetable
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URI", 'sqlite:///cart.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialisation de l'extension SQLAlchemy avec notre application
db.init_app(app)

# Création des tables au démarrage de l'application
@app.before_request
def create_tables():
    app.before_request_funcs[None].remove(create_tables)
    
    db.create_all()

# Ajout de quelques produits pour tester
@app.before_request
def add_sample_data():
    app.before_request_funcs[None].remove(add_sample_data)
    
    # Vérifier si des produits existent déjà
    if Produit.query.count() == 0:
        products = [
            Produit(nom='Smartphone Ultra', categorie="Smartphones", description='Smartphone pliable', prix=799.99, quantite_stock=50),
            Produit(nom='Casque Bluetooth', categorie="Casques audios", description='Audio haute qualité', prix=129.99, quantite_stock=30),
            Produit(nom='Livre Python', categorie="Livres", description='Apprendre Python en profondeur', prix=39.99, quantite_stock=100)
        ]
        db.session.add_all(products)
        
        # Créer un panier vide
        # cart = Cart()
        # db.session.add(cart)
        
        db.session.commit()

    # Compte administrateur de test, créé une seule fois
    if Utilisateur.query.filter_by(role=UserRole.ADMIN).first() is None:
        admin = Utilisateur(email="admin@digimarket.fr", role=UserRole.ADMIN)
        admin.set_password("Admin1234!")
        db.session.add(admin)
        db.session.commit()


## Auth
def generate_token(user: Utilisateur):
    return jwt.encode(
        # payload to encode
        {
            "exp": datetime.now(timezone.utc) + timedelta(hours=1), # expiration date of the token
            "role": user.role,
            "sub": str(user.id)
        }, 
        # secret used to generate the token and decode it --> that's the part that needs to be stored 
        JWT_SECRET, 
        # the algorithm that will be used to generate the token
        algorithm="HS256"
    )

def decode_token(token):
    try:
        return jwt.decode(
            token,
            JWT_SECRET,
            algorithms="HS256"
        )
    except Exception:
        print("Jeton JWT invalide.")
        return

# A decorator to check the authentification is valid for each path
def require_authentification(func): 
    @wraps(func)
    def wrapper(*args, **kwargs):
        scheme, _, token = request.headers.get("Authorization", "").partition(" ")

        # decode_token renvoie None si le jeton est illisible, expiré ou forgé
        payload = decode_token(token) if scheme == "Bearer" and token else None

        if payload is None:
            return jsonify({"error": "Token manquant ou invalide"}), 401

        g.user_id = payload["sub"]
        g.user_role = payload["role"]

        return func(*args, **kwargs)
    
    return wrapper

# Another decorator to check if the logged user is admin
def admin_required(func):
    """Autorisation : vérifie le token PUIS le rôle administrateur."""
    @wraps(func)
    @require_authentification
    def wrapper(*args, **kwargs):
        if g.user_role != UserRole.ADMIN:
            return jsonify({"error": "Accès réservé aux administrateurs"}), 403
        return func(*args, **kwargs)
    return wrapper

@app.route('/api/auth/register', methods=["POST"])
def register():
    body = request.get_json()
    check_auth_required_fields(body)

    user = Utilisateur.query.filter_by(email=body["email"]).first()

    if user is not None:
        return jsonify({"error": "cet email est déjà associé à un compte existant"}), 400

    new_user = Utilisateur(email=body.get("email"))
    new_user.set_password(body.get("password"))

    db.session.add(new_user)
    db.session.commit()

    return jsonify(new_user.to_dict()), 201


@app.route('/api/auth/login', methods=["POST"])
def login():
    body = request.get_json()
    check_auth_required_fields(body)

    user = Utilisateur.query.filter_by(email=body["email"]).first()

    if user is None:
        return jsonify({"error": "l'utilisateur n'est pas connu. Veuillez créer un compte"}), 400

    if not user.check_password(body["password"]):
        return jsonify({"error": "le mot de passe est incorrect"}), 400

    return jsonify({"token": generate_token(user), "user": user.to_dict()}), 200

@app.route('/api/produits', methods=["GET"])
def list_products():
    products = Produit.query.all()
    return jsonify({"products": [p.to_dict() for p in products]}), 200

@app.route('/api/produits/<int:id>', methods=["GET"])
def get_product(id):
    product = Produit.query.filter_by(id=id).first()

    if product is None:
        return jsonify({"error": "le produit cherché n'existe pas"}), 404

    return jsonify({"product": product.to_dict()}), 200

@app.route('/api/produits', methods=["POST"])
@admin_required
def create_product():
    body = request.get_json()
    check_product_required_fields(body)

    new_product = Produit(
        nom=body.get("nom"), 
        categorie=body.get("categorie"), 
        prix=body.get("prix"),
        quantite_stock=body.get("quantite_stock", None),
        description=body.get("description", None),
        )

    db.session.add(new_product)
    db.session.commit()

    return jsonify(new_product.to_dict()), 201

@app.route('/api/produits/<int:id>', methods=["PUT"])
@admin_required
def modify_product(id):
    body = request.get_json()
    check_product_required_fields(body)

    product = Produit.query.filter_by(id=id).first()

    if product is None:
        return jsonify({"error": "le produit à modifier n'existe pas"}), 404

    product.nom = body.get("nom")
    product.categorie = body.get("categorie")
    product.prix = body.get("prix")
    product.quantite_stock = body.get("quantite_stock", 0)
    product.description = body.get("description")

    db.session.commit()

    return jsonify({"product": product.to_dict()}), 200

@app.route('/api/produits/<int:id>', methods=["DELETE"])
@admin_required
def delete_product(id):
    product = Produit.query.filter_by(id=id).first()

    if product is None:
        return jsonify({"error": "le produit à supprimer n'existe pas"}), 404

    db.session.delete(product)
    db.session.commit()

    return jsonify({"message": "produit supprimé"}), 200

@app.route('/api/commandes', methods=['POST'])
@require_authentification
def create_order():
    body = request.get_json()
    check_order_required_fields(body)

    new_order = Commande(
        utilisateur_id=int(g.user_id),
        adresse_livraison=body.get("adresse_livraison")
    )

    for lignecommande in body['lignecommandes']:
        # Better to use db.session for primary key relation as select won't run again if information is already in session
        produit = db.session.get(Produit, lignecommande["produit_id"])

        # En cas d'erreur, on annule les stocks déjà décrémentés par les lignes précédentes
        if produit is None:
            db.session.rollback()
            return jsonify({"error": f"produit {lignecommande['produit_id']} introuvable"}), 404
        if produit.quantite_stock < lignecommande["quantite"]:
            db.session.rollback()
            return jsonify({"error": f"stock insuffisant pour {produit.nom}"}), 400

        produit.quantite_stock -= lignecommande["quantite"]
        new_order.lignecommandes.append(
            LigneCommande(
                produit_id=produit.id,
                quantite=lignecommande["quantite"],
                prix_unitaire=produit.prix,
            )
        )

    db.session.add(new_order)
    db.session.commit()

    return jsonify(new_order.to_dict()), 201

@app.route('/api/commandes', methods=['GET'])
@require_authentification
def list_orders():
    if g.user_role == UserRole.ADMIN:
        orders = Commande.query.all()

    else:
        orders = Commande.query.filter_by(utilisateur_id=int(g.user_id)).all()
    
    return jsonify([order.to_dict() for order in orders]), 200

@app.route('/api/commandes/<int:id>', methods=['GET'])
@require_authentification
def get_order(id):
    order = db.session.get(Commande, id)

    if order is None:
        return jsonify({"error": "la commande cherchée n'existe pas"}), 404

    # Un client ne peut consulter que ses propres commandes
    if g.user_role != UserRole.ADMIN and order.utilisateur_id != int(g.user_id):
        return jsonify({"error": "Accès interdit à cette commande"}), 403

    return jsonify(order.to_dict()), 200

@app.route('/api/commandes/<int:id>', methods=['PATCH'])
@admin_required
def update_order_status(id):
    body = request.get_json()
    check_order_status_field(body)

    order = db.session.get(Commande, id)

    if order is None:
        return jsonify({"error": "la commande à modifier n'existe pas"}), 404

    order.statut = OrderStatus(body["statut"])
    db.session.commit()

    return jsonify(order.to_dict()), 200

@app.route('/api/commandes/<int:id>/lignes', methods=['GET'])
@require_authentification
def list_order_lines(id):
    order = db.session.get(Commande, id)

    if order is None:
        return jsonify({"error": "la commande cherchée n'existe pas"}), 404

    if g.user_role != UserRole.ADMIN and order.utilisateur_id != int(g.user_id):
        return jsonify({"error": "Accès interdit à cette commande"}), 403

    return jsonify({"lignes": [ligne.to_dict() for ligne in order.lignecommandes]}), 200
