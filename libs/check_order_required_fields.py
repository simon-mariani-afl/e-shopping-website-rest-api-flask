from flask import abort, jsonify, make_response

ORDER_REQUIRED_FIELDS = ["adresse_livraison", "lignecommandes"]
ORDER_LINE_REQUIRED_FIELDS = ["produit_id", "quantite"]


def _is_positive_int(value):
    # bool hérite de int : on l'exclut explicitement (True == 1)
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def check_order_required_fields(body):
    if (
        not isinstance(body, dict)
        or any(not body.get(field) for field in ORDER_REQUIRED_FIELDS)
        or not isinstance(body["adresse_livraison"], str)
        or not isinstance(body["lignecommandes"], list)
        or any(
            not isinstance(lignecommande, dict)
            or any(not _is_positive_int(lignecommande.get(field)) for field in ORDER_LINE_REQUIRED_FIELDS)
            for lignecommande in body["lignecommandes"]
        )
    ):
        abort(make_response(
            jsonify({"error": "information manquante ou invalide pour créer la commande"}),
            400
        ))
