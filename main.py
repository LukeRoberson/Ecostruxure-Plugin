"""
Module: main.py

The EcoStruxure plugin
    Receives and processes webhooks from the SE EcoStruxure platform.
    This is for power management, such as UPS and PDU devices.

Usage:
    This is a Flask application that should run behind a WSGI server inside
        a Docker container.
    Build the Docker image and run it with the provided Dockerfile.

Functions:
    - logging_setup:
        Sets up the root logger for the web service.
    - create_app:
        Creates the Flask application instance and sets up the configuration.

Routes:
    - /api/health:
        Health check endpoint to ensure the service is running.
    - webhook:
        Handles webhook requests, validates them, and processes events.

Dependencies:
    - Flask: For creating the web application.
    - Flask-Session: For session management.
    - yaml: For loading configuration files.
    - logging: For logging messages to the terminal.
    - os: For environment variable access.

Custom dependencies:
    - event_handler: Custom module to handle webhook events from Cloudflare.
    - sdk: Custom module to manage configuration and other SDK-related tasks.
"""

# Standard library imports
from flask import (
    Flask,
    request,
    jsonify,
    make_response
)
from flask_session import Session
import yaml
import logging
import os

# Custom module imports
from event_handler import EventHandler
from sdk import Config, SystemLog


CONFIG_URL = "http://core:5100/api/config"
LOG_URL = "http://logging:5100/api/log"
PLUGINS_URL = "http://web-interface:5100/api/plugins"
HASH_URL = "http://security:5100/api/hash"


def logging_setup(
    config: dict,
) -> None:
    """
    Set up the root logger for the web service.

    Args:
        config (dict): The global configuration dictionary

    Returns:
        None
    """

    # Get the logging level from the configuration (eg, "INFO")
    log_level_str = config['web']['logging-level'].upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    # Set up the logging configuration
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logging.info("Logging setup complete with level: %s", log_level)


def create_app(
    system_log: SystemLog,
    plugin_config: dict,
) -> Flask:
    """
    Create the Flask application instance and set up the configuration.
    Registers the necessary blueprints for the web service.

    Args:
        system_log (SystemLog): An instance of SystemLog for logging.

    Returns:
        Flask: The Flask application instance.
    """

    # Create the Flask application
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('api_master_pw')
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = '/app/flask_session'
    app.config['SYSTEM_LOG'] = system_log
    app.config['PLUGIN_CONFIG'] = plugin_config
    Session(app)

    return app


# Load the plugin configuration file
with open('config.yaml', 'r') as f:
    config_data = yaml.safe_load(f)

# Set up the application
global_config = {}
with Config(CONFIG_URL) as config:
    global_config = config.read()
logging_setup(global_config)

# Initialize the SystemLog with default values
#   Values can be overridden when sending a log
system_log = SystemLog(
    logging_url=LOG_URL,
    source="ecostruxure-plugin",
    destination=["web"],
    group="plugin",
    category="EcoStruxure",
    alert="system",
    severity="info",
    teams_chat_id=config_data.get('chats', None).get('default', None)
)

app = create_app(
    system_log=system_log,
    plugin_config=config_data,
)


@app.route(
    '/api/health',
    methods=['GET']
)
def health():
    """
    Health check endpoint.
    Returns a JSON response indicating the service is running.
    """

    return jsonify({'status': 'ok'})


@app.route('/webhook', methods=['POST'])
def webhook():
    '''
    Handle incoming webhook requests from EcoStruxure.

    Returns:
        str: A response indicating the result of the processing.
    '''

    # Parse the incoming webhook request
    body = request.get_json()
    if not body:
        logging.error("No JSON body received.")
        return make_response(
            jsonify(
                {
                    'result': 'error',
                    'message': 'No JSON body received.'
                }
            ),
            400
        )

    # Parse the event
    with EventHandler(config=config_data) as event_handler:
        event_handler.process_event(
            event=body,
            headers=dict(request.headers),
        )

    return "Received", 200
