from flask import (
    Blueprint,
    request,
    jsonify,
    current_app
)

from app import ftp_client
from app.celery.tasks import send_files_to_dvla

sender_blueprint = Blueprint('send', __name__)


@sender_blueprint.route('/send', methods=['POST'])
def send_file():
    filename = request.args.get('filename')
    ftp_client.send_file("/tmp/" + filename)
    return jsonify(result="success", filename=filename), 200


@sender_blueprint.route('/test-queue', methods=['GET'])
def test_queue():
    send_files_to_dvla.apply_async(["BUCKET", ["1", "2", "3", "4", "5"]], queue="process-ftp")
    return jsonify(result="success"), 200
