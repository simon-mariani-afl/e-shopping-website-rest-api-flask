from flask import abort, jsonify, make_response

AUTH_REQUIRED_FIELDS = ["email", "password"]


def check_auth_required_fields(body):
    """Vérifie que le corps de la requête contient l'email et le mot de passe.

    Interrompt immédiatement la requête avec une erreur 400 (JSON) si un champ
    manque : l'appelant n'a rien à vérifier.
    """
    if not body or any(not body.get(field) for field in AUTH_REQUIRED_FIELDS):
        abort(make_response(
            jsonify({"error": "l'email et/ou le mot de passe sont manquants"}),
            400
        ))
