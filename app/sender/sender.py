from flask import (
    Blueprint,
    jsonify,
    current_app
)

from app import ftp_client

sender_blueprint = Blueprint('send', __name__)


@sender_blueprint.route('/send', methods=['POST'])
def send_file():
    ftp_client.send_file("/tmp/filename.txt")
    return jsonify(result="success"), 200
