"""Tests des modèles User et Product."""
from models import Product, User, UserRole, db


## User : mot de passe
def test_set_password_ne_stocke_pas_le_mot_de_passe_en_clair():
    user = User(email="a@b.fr")
    user.set_password("Motdepasse1!")

    assert user.password_hash is not None
    assert "Motdepasse1!" not in user.password_hash


def test_check_password_reconnait_le_bon_mot_de_passe():
    user = User(email="a@b.fr")
    user.set_password("Motdepasse1!")

    assert user.check_password("Motdepasse1!") is True


def test_check_password_refuse_un_mauvais_mot_de_passe():
    user = User(email="a@b.fr")
    user.set_password("Motdepasse1!")

    assert user.check_password("motdepasse1!") is False
    assert user.check_password("") is False


def test_set_password_produit_un_hash_different_a_chaque_fois():
    """Le sel rend deux hachages du même mot de passe différents."""
    premier, second = User(email="a@b.fr"), User(email="c@d.fr")
    premier.set_password("Motdepasse1!")
    second.set_password("Motdepasse1!")

    assert premier.password_hash != second.password_hash


## User : rôle et sérialisation
def test_le_role_par_defaut_est_client(flask_app):
    user = User(email="defaut@digimarket.fr")
    user.set_password("Motdepasse1!")
    db.session.add(user)
    db.session.commit()

    assert user.role == UserRole.CLIENT


def test_le_role_admin_est_conserve_en_base(flask_app):
    user = User(email="chef@digimarket.fr", role=UserRole.ADMIN)
    user.set_password("Motdepasse1!")
    db.session.add(user)
    db.session.commit()

    relu = User.query.filter_by(email="chef@digimarket.fr").first()
    assert relu.role == UserRole.ADMIN


def test_user_to_dict_nexpose_pas_le_hash(flask_app, customer):
    dictionnaire = customer.to_dict()

    assert set(dictionnaire) == {"id", "email", "role"}
    assert dictionnaire["id"] == str(customer.id)
    assert dictionnaire["role"] == UserRole.CLIENT


def test_user_repr_contient_lemail():
    assert "a@b.fr" in repr(User(email="a@b.fr"))


## Product
def test_product_to_dict_expose_tous_les_champs(flask_app, product):
    assert product.to_dict() == {
        "id": str(product.id),
        "name": "Clavier mécanique",
        "description": "Switches rouges, rétroéclairé",
        "category": "Périphériques",
        "price": 89.99,
        "stock": 25,
    }


def test_product_recoit_un_id_a_linsertion(flask_app, product):
    assert product.id is not None
    assert str(product.id) in product.to_dict()["id"]


def test_product_stock_vaut_zero_par_defaut(flask_app):
    """La colonne stock a un default=0 appliqué à l'insertion."""
    produit = Product(name="Goodie", category="Divers", price=5.0)
    db.session.add(produit)
    db.session.commit()

    assert produit.stock == 0


def test_product_description_est_optionnelle(flask_app):
    produit = Product(name="Goodie", category="Divers", price=5.0)
    db.session.add(produit)
    db.session.commit()

    assert produit.description is None


def test_product_repr_contient_le_nom():
    assert "Clavier" in repr(Product(name="Clavier", category="Divers", price=1.0))
