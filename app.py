from flask import Flask, render_template, request, redirect, url_for, flash, session
from bcrypt import hashpw, gensalt, checkpw

app = Flask(__name__)

# CONFIG: config.py (For this we installed python-dotenv in our venv)
from dotenv import load_dotenv
import os

load_dotenv()

# config is a dictionary inside Flask
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS')

from models.models import db, Registrations, Subjects, Chapters, Quizzes, Questions, UserInput, Scores

# ROUTES: routes.py
@app.route('/login')
def login():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login_post():
    username = request.form.get("username")
    password = request.form.get("password")

    user = Registrations.query.filter_by(username=username).first()

    if not user:
        flash("Username does not exist!", "error")
        return redirect(url_for("login"))
    
    if not checkpw(password.encode('utf-8'), user.passhash):
        flash("Incorrect password!", "error")
        return redirect(url_for("login"))
    
    session["user_id"] = user.id
    if user.is_admin:
        flash("Welcome admin!", "error")
    else:
        flash("Login succesful!", "error")
    return redirect(url_for("home"))

@app.route("/registration")
def registration():
    return render_template("register.html")

@app.route("/registration", methods=["POST"])
def registration_post():
    fullname = request.form.get("fullname")
    username = request.form.get("username")
    email = request.form.get("email")
    dob = request.form.get("dob")
    password = request.form.get("password")
    cf_password = request.form.get("cf_password")
    pursuing = request.form.get("pursuing")

    if password != cf_password:
        flash("Re-entered password does not match, please enter your password again.", "error")
        return redirect(url_for("registration"))
    
    username_check = Registrations.query.filter_by(username=username).first()

    if username_check:
        flash("Username already exists, create another.", "error")
        return redirect(url_for("registration"))
    
    salt = gensalt()
    password_hash = hashpw(password.encode('utf-8'), salt)

    email_check = Registrations.query.filter_by(email=email).first()

    if email_check:
        flash("Email already registered. Please use a different email.", "error")
        return redirect(url_for("registration"))

    new_user = Registrations(fullname=fullname, username=username, email=email, dob=dob, passhash=password_hash, pursuing=pursuing)
    db.session.add(new_user) #no need to worry about starting/ending the session, as we are using ORM of SQLAlchemy and not SQL Query
    db.session.commit()
    return redirect(url_for("login"))
    
if  __name__ == "__main__":
    app.run(debug=True)