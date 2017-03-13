from flask import (
    Blueprint,
    jsonify,
    current_app
)

status_blueprint = Blueprint('status', __name__)


@status_blueprint.route('/_status', methods=['GET'])
def test():
    return jsonify(result="success"), 200
