from flask import abort, jsonify, make_response

from models import OrderStatus

ORDER_STATUSES = [status.value for status in OrderStatus]


def check_order_status_field(body):
    if not isinstance(body, dict) or body.get("statut") not in ORDER_STATUSES:
        abort(make_response(
            jsonify({"error": f"statut manquant ou invalide, valeurs possibles : {', '.join(ORDER_STATUSES)}"}),
            400
        ))
