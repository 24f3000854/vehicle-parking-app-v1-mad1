import os
from flask import Flask
from application.database import db
from application.models import *


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL", "sqlite:////tmp/vehicle-parking.sqlite3"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")

    #for vercel deployment
    temp_instance_path = "/tmp/vehicle-parking-instance"
    os.makedirs(temp_instance_path, exist_ok=True)
    app.instance_path = temp_instance_path

    db.init_app(app)

    with app.app_context():
        db.create_all()

    return app


app = create_app()
app.app_context().push()

import application.controllers


if __name__ == "__main__":
    app.run(debug=True)