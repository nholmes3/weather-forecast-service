import logging

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_apscheduler import APScheduler

db = SQLAlchemy()
scheduler = APScheduler()

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


def create_app(config_class='config.Config'):
    app = Flask(__name__)

    # set logging
    app.logger.setLevel(logging.DEBUG)

    # add config
    app.config.from_object(config_class)

    # Register endpoints
    from app.endpoints import endpoints_bp
    app.register_blueprint(endpoints_bp)

    # init db
    db.init_app(app)

    # init scheduler
    scheduler.init_app(app)

    from app import models, tasks, endpoints

    return app
