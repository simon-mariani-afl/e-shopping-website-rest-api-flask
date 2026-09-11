from flask import abort, jsonify, make_response

PRODUCT_REQUIRED_FIELDS = ["name", "category", "price"]


def check_product_required_fields(body):
    """Vérifie que le corps de la requête contient les champs obligatoires d'un produit.

    Interrompt immédiatement la requête avec une erreur 400 (JSON) si un champ
    manque : l'appelant n'a rien à vérifier.
    """
    if not body or any(not body.get(field) for field in PRODUCT_REQUIRED_FIELDS):
        abort(make_response(
            jsonify({"error": "information manquante pour créer le produit"}),
            400
        ))
