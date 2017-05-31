from flask import (
    Blueprint,
    request,
    jsonify,
    current_app
)

from app import ftp_client
from app.celery.tasks import send_files_to_dvla
from app.files.file_utils import (
    get_file_from_s3,
    create_local_file_directory,
    concat_files,
    ensure_local_file_directory
)
from app.celery.tasks import send_files_to_dvla

sender_blueprint = Blueprint('send', __name__)


@sender_blueprint.route('/send', methods=['POST'])
def send_file():
    filename = request.args.get('filename')
    ftp_client.send_file("/tmp/" + filename)
    return jsonify(result="success", filename=filename), 200


@sender_blueprint.route('/test-s3', methods=['GET'])
def test_s3():
    request.args.getlist('job_id')
    send_files_to_dvla.apply_async([request.args.getlist('job_id')], queue='process-ftp-tasks')
    return jsonify(result="success"), 200
