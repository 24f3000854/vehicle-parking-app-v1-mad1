from flask import Flask, render_template, redirect, request
from flask import current_app as app  # if u directly import the app, it leadds to cirular loop and go to erroer
#current_app refers to app object(app.py)
#everywhere we can use as app
from .models import *
# Importing the models to use in the controllers
