from flask import Flask, render_template, redirect, request
from flask import current_app as app  # if u directly import the app, it leadds to cirular loop and go to erroer
#current_app refers to app object(app.py)
#everywhere we can use as app
from .models import *
# Importing the models to use in the controllers


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        pwd = request.form["pwd"] 
        this_user = User.query.filter_by(email = email).first()  #left table is User, right table is form data
        if this_user:
            if this_user.pwd == pwd:
                if this_user.type == "admin":
                    return render_template("admin_dashboard.html",this_user=this_user)
                else:
                    return render_template("user_dashboard.html", this_user=this_user)
            else:
                return "password is incorrect"
        else:
            return "email(user) does not exist"
    return render_template("login.html")
 
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        email = request.form["email"]
        confirm_email = request.form["confirm_email"]
        vehicle_reg = request.form["vehicle_reg"]
        pincode = request.form["pincode"]
        phone_number = request.form["phone_number"]
        pwd = request.form["pwd"]
        confirm_password = request.form["confirm_pwd"]
        gender = request.form.get("gender")
        age = request.form["age"]
        if email != confirm_email:
            return "Email addresses do not match"
        if pwd != confirm_password:
            return "Passwords do not match"
        user_email = User.query.filter_by(email=email).first()
        if user_email:
            return "Email already registered"
        else:
            new_user = User(first_name=first_name,last_name=last_name, email=email, pwd=pwd, vehicle_reg=vehicle_reg, pincode=pincode, phone_number=phone_number, gender=gender, age=age)
            db.session.add(new_user)
            db.session.commit()
        return "Registered successfully <a href='/login'>Login</a>"
    return render_template("register.html")
