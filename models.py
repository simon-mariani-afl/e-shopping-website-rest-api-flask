from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid
from enum import Enum

# Initialisation de l'extension SQLAlchemy
db = SQLAlchemy()

# Énumération des rôles
class UserRole(str, Enum):
    CLIENT = "client"
    ADMIN = "admin"

# Définition des modèles
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Uuid, primary_key=True, default=uuid.uuid4)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.CLIENT)

    def __repr__(self):
        return f'<User {self.email}>'

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def set_password(self, password): 
        self.password_hash = generate_password_hash(password)

    def to_dict(self):
        return {"id": str(self.id), "email": self.email, "role": self.role}

class Product(db.Model):

    __tablename__ = 'product'
    
    id = db.Column(db.Uuid, primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<Product {self.name}>'

    def to_dict(self):
        return {"id": str(self.id), "name": self.name, "description": self.description, "category": self.category, "price": self.price, "stock": self.stock}

# class Cart(db.Model):
#     __tablename__ = 'carts'
    
#     id = db.Column(db.Integer, primary_key=True)
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
#     # Relation avec les éléments du panier
#     # cascade = 'all, delete-orphans' indique que lorsqu'un panier est dupprimé, tous ses éléments le sont aussi
#     items = db.relationship('CartItem', backref='cart', lazy=True, cascade='all, delete-orphan')
    
#     def __repr__(self):
#         return f'<Cart {self.id}>'

# class CartItem(db.Model):
#     __tablename__ = 'cart_items'
    
#     id = db.Column(db.Integer, primary_key=True)
#     cart_id = db.Column(db.Integer, db.ForeignKey('carts.id'), nullable=False)
#     product_id = db.Column(db.String(10), db.ForeignKey('products.id'), nullable=False)
#     quantity = db.Column(db.Integer, default=1)
    
#     # Relation avec le produit
#     # backref : vers quelle classe la classe cible va ici pointer
#     # lazy = True  définit comment les données associées seront chargées - True = différées
#     product = db.relationship('Product', backref='cart_items')
    
#     def __repr__(self):
#         return f'<CartItem {self.id}, Product: {self.product_id}, Qty: {self.quantity}>'