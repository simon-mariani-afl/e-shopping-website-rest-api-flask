import jwt
from flask import Flask, request, jsonify, g
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from functools import wraps
import os
import uuid

from models import User, Product, UserRole, db

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")

app = Flask(__name__)

# Configuration de la base de données
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cart.db'
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
    if Product.query.count() == 0:
        products = [
            Product(name='Smartphone Ultra', category="Smartphones", description='Smartphone pliable', price=799.99, stock=50),
            Product(name='Casque Bluetooth', category="Casques audios", description='Audio haute qualité', price=129.99, stock=30),
            Product(name='Livre Python', category="Livres", description='Apprendre Python en profondeur', price=39.99, stock=100)
        ]
        db.session.add_all(products)
        
        # Créer un panier vide
        # cart = Cart()
        # db.session.add(cart)
        
        db.session.commit()

    # Compte administrateur de test, créé une seule fois
    if User.query.filter_by(role=UserRole.ADMIN).first() is None:
        admin = User(email="admin@digimarket.fr", role=UserRole.ADMIN)
        admin.set_password("Admin1234!")
        db.session.add(admin)
        db.session.commit()


## Auth
def generate_token(user: User):
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
        token = request.headers.get("Authorization", "0")

        try:
            payload = decode_token(token.split(" ", 1)[1])   # (1) on GARDE le payload
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expiré"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Token invalide"}), 401

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
    if not body or not body.get("email") or not body.get("password"):
            return jsonify({"error": "l'email et/ou le mot de passe sont manquants"}), 400

    user = User.query.filter_by(email=body["email"]).first()

    if user is not None: 
        return jsonify({"error": "cet email est déjà associé à un compte existant"}), 400

    new_user = User(email=body.get("email"))
    new_user.set_password(body.get("password"))

    db.session.add(new_user)
    db.session.commit()

    return jsonify(new_user.to_dict()), 201


@app.route('/api/auth/login', methods=["POST"])
def login():
    body = request.get_json()
    if not body or not body.get("email") or not body.get("password"):
        return jsonify({"error": "l'email et/ou le mot de passe sont manquants"})

    user = User.query.filter_by(email=body["email"]).first()

    if user is None:
        return jsonify({"error": "l'utilisateur n'est pas connu. Veuillez créer un compte"}), 400

    if not user.check_password(body["password"]):
        return jsonify({"error": "le mot de passe est incorrect"}), 400

    return jsonify({"token": generate_token(user), "user": user.to_dict()}), 200

@app.route('/api/produits', methods=["GET"])
def list_products():
    products = Product.query.all()
    return jsonify({"products": [p.to_dict() for p in products]}), 200

@app.route('/api/produits/{id}', methods=["GET"])
def get_product(id):
    product = Product.query.filter_by(id=id).first()

    if product is None: 
        return jsonify({"error": "le produit cherché n'existe pas"})
    
    return jsonify({"product": product.to_dict()}), 200

@app.route('/api/produits', methods=["POST"])
@admin_required
def create_product():
    body = request.get_json()
    if not body or not body.get("name") or not body.get("category") or not body.get("price"):
        return jsonify({"error": "information manquante pour créer le produit"})

    new_product = Product(
        name=body.get("name"), 
        category=body.get("category"), 
        price=body.get("price"),
        stock=body.get("stock", None),
        description=body.get("description", None),
        )

    db.session.add(new_product)
    db.session.commit()

    return jsonify(new_product.to_dict()), 201

# @app.route('/api/produits/{id}', methods=["PUT"])
# @app.route('/api/produits', methods=["DELETE"])
    