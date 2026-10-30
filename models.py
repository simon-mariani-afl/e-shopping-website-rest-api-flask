from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from enum import Enum

# Initialisation de l'extension SQLAlchemy
db = SQLAlchemy()

# Énumération des rôles
class UserRole(str, Enum):
    CLIENT = "client"
    ADMIN = "admin"

class OrderStatus(str, Enum):
    EN_ATTENTE = "en_attente"
    VALIDEE = "validee"
    EXPEDIEE = "expediee"
    ANNULEE = "annulee"

# Définition des modèles
class Utilisateur(db.Model):
    __tablename__ = 'utilisateur'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    mot_de_passe = db.Column(db.String(255), nullable=False)
    nom = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.CLIENT)
    date_creation = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<Utilisateur {self.nom}>'

    def check_password(self, password):
        return check_password_hash(self.mot_de_passe, password)

    def set_password(self, password): 
        self.mot_de_passe = generate_password_hash(password)

    def to_dict(self):
        return {"id": self.id, "email": self.email, "role": self.role}

class Produit(db.Model):

    __tablename__ = 'produit'
    
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    categorie = db.Column(db.String(255), nullable=False)
    prix = db.Column(db.Float, nullable=False)
    quantite_stock = db.Column(db.Integer, default=0) 
    date_creation = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<Produit {self.nom}>'

    def to_dict(self):
        return {"id": self.id, "nom": self.nom, "description": self.description, "categorie": self.categorie, "prix": self.prix, "quantite_stock": self.quantite_stock}

class Commande(db.Model):

    __tablename__ = 'commande'

    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=False)
    date_commande = db.Column(db.DateTime, default=datetime.now)
    adresse_livraison = db.Column(db.String(255), nullable=False)
    statut = db.Column(db.Enum(OrderStatus), nullable=False, default=OrderStatus.EN_ATTENTE)

    utilisateur = db.relationship('Utilisateur', backref='commandes')
    lignecommandes = db.relationship('LigneCommande', backref='commande', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Commande {self.id}>'

    def total(self):
        return round(sum(ligne.quantite * ligne.prix_unitaire for ligne in self.lignecommandes), 2)

    def to_dict(self):
        return {
            "id": self.id,
            "utilisateur_id": self.utilisateur_id,
            "date_commande": self.date_commande.isoformat() if self.date_commande else None,
            "adresse_livraison": self.adresse_livraison,
            "statut": self.statut.value,
            "lignes": [ligne.to_dict() for ligne in self.lignecommandes],
            "total": self.total(),
        }

class LigneCommande(db.Model):

    __tablename__ = 'lignecommande'

    id = db.Column(db.Integer, primary_key=True)
    commande_id = db.Column(db.Integer, db.ForeignKey('commande.id'), nullable=False)
    produit_id = db.Column(db.Integer, db.ForeignKey('produit.id'), nullable=False)
    quantite = db.Column(db.Integer, nullable=False, default=1)
    prix_unitaire = db.Column(db.Float, nullable=False)

    produit = db.relationship('Produit', backref='lignes_commande')

    def __repr__(self):
        return f'<LigneCommande {self.id}>'

    def to_dict(self):
        return {
            "id": self.id,
            "produit_id": self.produit_id,
            "quantite": self.quantite,
            "prix_unitaire": self.prix_unitaire,
            "sous_total": round(self.quantite * self.prix_unitaire, 2),
        }
