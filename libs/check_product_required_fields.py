from flask import abort, jsonify, make_response

PRODUCT_REQUIRED_FIELDS = ["nom", "categorie", "prix"]


def check_product_required_fields(body):
    if not body or any(not body.get(field) for field in PRODUCT_REQUIRED_FIELDS):
        abort(make_response(
            jsonify({"error": "information manquante pour créer le produit"}),
            400
        ))
