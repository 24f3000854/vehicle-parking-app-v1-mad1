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
    db.init_app(app)

    with app.app_context():
        db.create_all()

    return app


app = create_app()
app.app_context().push()

from application.controllers import *


if __name__ == "__main__":
    app.run(debug=True)