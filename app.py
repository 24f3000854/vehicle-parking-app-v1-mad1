from flask import Flask
from application.database import db  #step 3 Import the db instance from database.py
app = None

def create_app():
    app= Flask(__name__) #app.py as a server ig
    app.debug = True #debug information mode on
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vehicle-parking.sqlite3'  # step 3 SQLite database file
    db.init_app(app)  # step 3Initialize the SQLAlchemy instance with the Flask app
    app.app_context().push() #this momdules will application telling server is consider this code refers to first line
    return app  

app = create_app() #create app instance                                                  
from application.controllers import *  # step 2 import all the controllers
#from application.models import *  # import all the models


if __name__ == '__main__':        # run my application
    app.run()