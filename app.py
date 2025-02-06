from flask import Flask, render_template, request, redirect, url_for, flash, session
from bcrypt import hashpw, gensalt, checkpw
from functools import wraps

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

def authentication(func): # decorator for authentication
    @wraps(func)
    def auth(*args, **kwargs):
        if 'user_id' in session:
            return func(*args, **kwargs)
        else:
            flash("Please login to continue", "error")
            return redirect(url_for("login"))
    return auth

@app.route("/login")
def login():
    return render_template("login.html", user=None)

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
        flash("Welcome admin!", "success")
        return redirect(url_for("admin"))
    else:
        flash("Login successful!", "success")
    return redirect(url_for("home"))

@app.route("/logout")
def logout():
    session.pop("user_id")
    flash("You have logged out.", "success")
    return redirect(url_for("login"))

@app.route("/registration")
def registration():
    return render_template("register.html", user=None)

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

@app.route("/home")
@authentication
def home():
    user = Registrations.query.get(session['user_id'])
    if user.is_admin:
        return redirect(url_for("admin", user=user))
    return render_template("home.html", user=user)

@app.route("/profile")
@authentication
def profile():
    return render_template("profile.html", user=Registrations.query.get(session['user_id']))

@app.route("/profile", methods=["POST"])
@authentication
def profile_post():
    username = request.form.get("username")
    curr_password = request.form.get("curr_password")
    password = request.form.get("password")

    if not username or not curr_password or not password:
        flash("Please fill all the fields", "error")
        return redirect(url_for("profile"))
    
    user = Registrations.query.get(session['user_id'])
    if not checkpw(curr_password.encode("utf-8"), user.passhash):
        flash("Incorrect password!", "error")
        return redirect(url_for("profile"))
    
    if username != user.username:
        new_username = Registrations.query.filter_by(username=username).first()
        if new_username:
            flash("Username already exists!", "error")
            return redirect(url_for("profile"))
        
    salt = gensalt()
    new_passhash = hashpw(password.encode("utf-8"), salt)
    user.username = username
    user.passhash = new_passhash
    db.session.commit()
    return redirect(url_for("profile"))

@app.route("/admin")
def admin():
    return render_template("admin.html", user=Registrations.query.get(session['user_id']))
    
if  __name__ == "__main__":
    app.run(debug=True)