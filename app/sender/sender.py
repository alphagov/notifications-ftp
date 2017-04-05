from flask import (
    Blueprint,
    request,
    jsonify,
    current_app
)

from app import ftp_client

sender_blueprint = Blueprint('send', __name__)


@sender_blueprint.route('/send', methods=['POST'])
def send_file():
    filename = request.args.get('filename')
    ftp_client.send_file("/tmp/" + filename)
    return jsonify(result="success", filename=filename), 200
