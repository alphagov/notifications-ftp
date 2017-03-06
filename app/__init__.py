import os
from monotonic import monotonic

from app.celery.celery import NotifyCelery
from flask import (
    Flask,
    request,
    jsonify,
    g,
    url_for
)
from notifications_utils.clients.statsd.statsd_client import StatsdClient

notify_celery = NotifyCelery()
statsd_client = StatsdClient()


def create_app():
    application = Flask(__name__)

    from app.config import configs

    notify_environment = os.environ['NOTIFY_ENVIRONMENT']

    application.config.from_object(configs[notify_environment])

    init_app(application)

    notify_celery.init_app(application)
    statsd_client.init_app(application)

    from app.status.status import status_blueprint

    application.register_blueprint(status_blueprint)

    return application


def init_app(app):
    @app.before_request
    def record_user_agent():
        statsd_client.incr("user-agent.{}".format(process_user_agent(request.headers.get('User-Agent', None))))

    @app.before_request
    def record_request_details():
        g.start = monotonic()
        g.endpoint = request.endpoint

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
        return response

    @app.errorhandler(Exception)
    def exception(e):
        return jsonify(result='error', message=str(e)), error.code or 500

    @app.errorhandler(404)
    def page_not_found(e):
        return jsonify(result='error', message=str(e)), 404


def process_user_agent(user_agent_string):
    if user_agent_string and user_agent_string.lower().startswith("notify"):
        components = user_agent_string.split("/")
        client_name = components[0].lower()
        client_version = components[1].replace(".", "-")
        return "{}.{}".format(client_name, client_version)
    elif user_agent_string and not user_agent_string.lower().startswith("notify"):
        return "non-notify-user-agent"
    else:
        return "unknown"
