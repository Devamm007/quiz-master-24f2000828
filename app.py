from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime, date
# from bcrypt import hashpw, gensalt, checkpw
from functools import wraps
from flask_login import LoginManager, UserMixin, login_required, current_user, logout_user, login_user

app = Flask(__name__)

# CONFIG: (For this we installed python-dotenv in our venv)
from dotenv import load_dotenv
from os import getenv

load_dotenv()

# config is a dictionary inside Flask
app.config['SECRET_KEY'] = getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = getenv('SQLALCHEMY_TRACK_MODIFICATIONS')

from models.models import db, Registrations, Subjects, Chapters, Quizzes, Questions, UserInput, Scores

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Registrations.query.get(int(user_id))

def admin_auth(func): # decorator for admin authentication
    @wraps(func)
    def auth(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please login to continue", "error")
            return redirect(url_for("login"))
        if not current_user.is_admin:
            flash("You are not authorized!", "error")
            return redirect(url_for("home"))
        return func(*args, **kwargs)
    return auth

def preprocess_value(value):
    if isinstance(value, str):
        return value.strip().lower()
    return value

def update(object, edit):
    try:
        for key, value in edit:
                if hasattr(object, key):
                    attr_type = type(getattr(object, key))
                    if attr_type == date:
                        setattr(object, key, datetime.strptime(value, "%Y-%m-%d").date())
                        continue
                    setattr(object, key, preprocess_value(value))
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred: {str(e)}", "error")
        return redirect(url_for("home"))

# ROUTES: routes.py
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html", user=None)

    if request.method == "POST":
        username = request.form.get("username").strip()
        password = request.form.get("password")

        user = Registrations.query.filter_by(username=username).first()

        if not user or not user.check_password(password):
            flash("Invalid username or password", "error")
            return redirect(url_for("login"))
    flash("Login successful!", "success")
    redirect(url_for("home"))    

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have logged out successfully.", "success")
    redirect(url_for("login"))

@app.route("/registration", methods=["GET", "POST"])
def registration():
    if request.method == "GET":
        return render_template("register.html", user=None)
    if request.method == "POST":
        username = request.form.get("username").strip()
        email = request.form.get("email").strip()
        dob = datetime.strptime(request.form.get("dob"), '%Y-%m-%d').date()
        password = request.form.get("password")
        cf_password = request.form.get("cf_password")

        if password != cf_password:
            flash("Re-entered password does not match, please enter your password again.", "error")
            return redirect(url_for("registration"))
        
        username_check = Registrations.query.filter_by(username=username).first()

        if username_check:
            flash("Username already exists, create another.", "error")
            return redirect(url_for("registration"))

        email_check = Registrations.query.filter_by(email=email).first()

        if email_check:
            flash("Email already registered. Please use a different email.", "error")
            return redirect(url_for("registration"))

        new_user = Registrations(fullname=request.form.get("fullname").strip().lower(), username=username,
                                 email=email, dob=dob, password=password,
                                 pursuing=request.form.get("pursuing")) # passhash=password_hash, pursuing=pursuing)
        db.session.add(new_user) #no need to worry about starting/ending the session, as we are using ORM of SQLAlchemy and not SQL Query
        db.session.commit()
    flash("Successfully registered.", "success")
    redirect(url_for("login"))

@app.route("/profile/delete", methods=["POST"])
@login_required
def delete_account():
    user = Registrations.query.get(current_user.id)
    if user.is_admin:
        flash("Admin's account cannot be deleted", "error")
        return redirect(url_for("profile"))
    if user:
        db.session.delete(user)
        db.session.commit()
        session.clear()
        flash("Your account has been successfully deleted.", "success")
        return redirect(url_for("login"))
    flash("User not found!", "error")
    redirect(url_for("profile"))

@app.route("/home")
@login_required
def home():
    user = Registrations.query.get(current_user.id)
    if user.is_admin:
        return redirect(url_for("admin", user=user))
    return render_template("home.html", user=user, quizzes=Quizzes.query.all(), 
                           chapters=Chapters.query.all(), subjects=Subjects.query.all(), 
                           questions=Questions.query.all())

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "GET":
        return render_template("profile.html", user=Registrations.query.get(current_user.id))
    if request.method == "POST":
        username = request.form.get("username").strip()
        curr_password = request.form.get("curr_password")
        password = request.form.get("password")

        if not username or not curr_password or not password:
            flash("Please fill all the fields", "error")
            return redirect(url_for("profile"))
        
        user = Registrations.query.get(current_user.id)

        if not user.check_password(curr_password):
            flash("Incorrect password!", "error")
            return redirect(url_for("profile"))
        
        if username != user.username:
            new_username = Registrations.query.filter_by(username=username).first()
            if new_username:
                flash("Username already exists!", "error")
                return redirect(url_for("profile"))
            
        user.username = username
        user.password = password
        db.session.commit()
        flash("Password updated!", "success")
        redirect(url_for("profile"))

@app.route("/admin")
@admin_auth
def admin():
    user=Registrations.query.get(current_user.id)
    subjects=Subjects.query.all()
    chapters=Chapters.query.all()
    return render_template('admin.html', user=user, subjects=subjects, chapters=chapters)

@app.route("/users")
@admin_auth
def users():
    user=Registrations.query.get(current_user.id)
    users = Registrations.query.filter_by(is_admin=False).all()
    return render_template("users_detail.html", users=users, user=user)

#SUBJECT
@app.route("/admin", methods=["POST"])
@admin_auth
def add_subject():
    subject = request.form.get("subject").strip().lower()
    subject_des = request.form.get("subject_des").strip()
    existing_subject = Subjects.query.filter_by(subject=subject).first()

    if existing_subject:
        flash("Subject already exist!", "error")
        return redirect(url_for("admin"))
    
    new_subject = Subjects(subject=subject, subject_des=subject_des)
    db.session.add(new_subject)
    db.session.commit()

    flash("Subject added successfully!", "success")
    return redirect(url_for("admin"))

@app.route("/admin/subject/<int:id>/edit", methods=["POST"])
@admin_auth
def edit_subject(id):
    subject = request.form.get("subject").strip().lower()

    old_subject = Subjects.query.get(id)
    existing_subject = Subjects.query.filter_by(subject=subject).first()

    if old_subject.subject != subject and existing_subject:
        flash("Subject already exist!", "error")
        return redirect(url_for("admin"))
        
    update(old_subject, request.form.items())

    flash("Subject updated successfully!", "success")
    return redirect(url_for("admin"))

#CHAPTER
@app.route("/admin/subject/<int:id>/add_chapter", methods=["POST"])
@admin_auth
def add_chapter(id):
    chapter = request.form.get("chapter").strip().lower()
    chapter_des = request.form.get("chapter_des").strip()
    existing_chapter = Chapters.query.filter_by(chapter=chapter).first()

    if existing_chapter:
        flash("Chapter already exist!", "error")
        return redirect(url_for("admin"))
    
    new_chapter = Chapters(subject_id=id, chapter=chapter, chapter_des=chapter_des)
    db.session.add(new_chapter)
    db.session.commit()

    flash("Chapter added successfully!", "success")
    return redirect(url_for("admin"))

@app.route("/admin/chapter/<int:id>/edit", methods=["POST"])
@admin_auth
def edit_chapter(id):
    chapter = request.form.get("chapter").strip().lower()

    old_chapter = Chapters.query.get(id)
    existing_chapter = Chapters.query.filter_by(chapter=chapter).first()

    if not existing_chapter and chapter != old_chapter.chapter:
        flash("Chapter already exist!", "error")
        return redirect(url_for("admin"))
        
    update(old_chapter, request.form.items())

    flash("Chapter updated successfully!", "success")
    return redirect(url_for("admin"))

#QUIZ
@app.route("/admin/quizzes")
@admin_auth
def quizzes():
    user=Registrations.query.get(session['user_id'])
    quizzes=Quizzes.query.all()
    questions=Questions.query.all()
    return render_template("quizzes.html", user=user, quizzes=quizzes, questions=questions)

@app.route("/admin/quizzes/<int:id>/view")
@admin_auth
def view_quiz(id):
    user=Registrations.query.get(session['user_id'])
    quiz = Quizzes.query.get(id)
    chapter = Chapters.query.get(quiz.chapter_id)
    subject = Subjects.query.get(chapter.subject_id)
    questions = Questions.query.filter_by(quiz_id=quiz.id)
    return render_template('quiz_details.html', user=user, quiz=quiz, subject=subject, chapter=chapter, questions=questions)

@app.route("/admin/quizzes/add", methods=["POST"])
@admin_auth
def add_quiz():
    chap_id = request.form.get("chap_id").strip()
    title = request.form.get("title").strip().lower()
    doa = datetime.strptime(request.form.get("doa"), '%Y-%m-%d').date()
    time = request.form.get("time")
    remarks = request.form.get("remarks")

    chapter = Chapters.query.get(chap_id)
    exisiting_quiz = Quizzes.query.filter_by(title=title).first()
    if exisiting_quiz:
        flash("Quiz already exists! Please add another Quiz.", "error")
    if not chapter:
        flash("Chapter with this ID does not exist! \nEnter a valid ID", "error")
        return redirect(url_for("quizzes"))
    if not chap_id:
        flash("Please enter Chapter ID", "error")
        return redirect(url_for("quizzes"))
    if not doa:
        flash("Please enter attempt date of quiz", "error")
        return redirect(url_for("quizzes"))
    if not time:
        flash("Please enter duration of quiz", "error")
        return redirect(url_for("quizzes"))    

    new_quiz = Quizzes(chapter_id=chap_id, title=title, doa=doa, time=time, remarks=remarks)
    db.session.add(new_quiz)
    db.session.commit()
    flash("Quiz added successfully", "success")
    return redirect(url_for("quizzes"))

@app.route("/admin/quizzes/<int:id>/edit", methods=["POST"])
@admin_auth
def edit_quiz(id):
    title = request.form.get("title").strip().lower()

    old_quiz = Quizzes.query.get(id)
    existing_quiz = Quizzes.query.filter_by(title=title).first()

    if not existing_quiz and title != old_quiz.title:
        flash("Chapter already exist!", "error")
        return redirect(url_for("admin"))
    
    update(old_quiz, request.form.items())
    flash("Quiz updated succesfully!", "success")
    return redirect(url_for("quizzes"))

#QUESTION
@app.route("/admin/quizzes/<int:id>/question/add", methods=["POST"])
@admin_auth
def add_question(id):
    # Only for single correct, did not implement multiple correct or numeric.
    question_type = request.form.get("question_type").strip()
    question = request.form.get("question").strip().lower()
    title = request.form.get("title").strip().lower()
    option1 = request.form.get("option1").strip()
    option2 = request.form.get("option2").strip()
    option3 = request.form.get("option3").strip()
    option4 = request.form.get("option4").strip()
    answer = request.form.get("answer").strip()
    weightage = int(request.form.get("weightage"))

    check = {"question":question, "title":title, "option1":option1, "option2":option2, "option3":option3, "option4":option4, "answer":answer}
    for k, v in check:
        if not v:
            flash(f"Please fill {k} field.", "error")
            return redirect(url_for("quizzes"))
    if not weightage or weightage==0 or weightage<0 or weightage>10:
        flash("Give valid weightage to question from 1-10 points", "error")
        return redirect(url_for("quizzes"))
    
    old_question_title = Questions.query.filter_by(title=title).first()
    old_question = Questions.query.filter_by(question=question).first()
    if old_question:
        flash("Question already exists", "error")
    if old_question_title:
        flash("Question with this title already exist", "error")
        return redirect(url_for("quizzes"))
    
    new_question = Questions(quiz_id=id, question=question, title=title, question_type=question_type, option1=option1, option2=option2, option3=option3, option4=option4, answer=answer, weightage=weightage)
    db.session.add(new_question)
    db.session.commit()
    flash("Question added successfully", "success")
    return redirect(url_for("quizzes"))

@app.route("/admin/question/<int:id>/edit", methods=["POST"])
@admin_auth
def edit_question(id):
    old_question = Questions.query.get(id)
    title = request.form.get("title").strip().lower()
    existing_question = Questions.query.filter_by(title=title)

    if not existing_question and old_question.title != title:
        flash("Question already exists.", "error")
        return redirect(url_for("quizzes"))

    if old_question.question_type == "single_correct":
        weightage = request.form.get("weightage")
        if int(weightage)==0 or int(weightage)<0 or int(weightage)>10:
            flash("Give valid weightage to question from 1-10 points", "error")
            return redirect(url_for("quizzes"))
        
    update(old_question, request.form.items())
    flash("Question updated successfully", "success")
    return redirect(url_for("quizzes"))

@app.route("/admin/<model>/<int:id>/delete", methods=["POST"])
@admin_auth
def del_model(model, id):
    models = {
        "subject": Subjects,
        "chapter": Chapters,
        "quiz": Quizzes,
        "question": Questions,
    }

    instance_to_delete = models[model].query.get(id)
    if instance_to_delete:
        db.session.delete(instance_to_delete)
        db.session.commit()
    flash(f"{model.capitalize()} deleted successfully!", "success")

    if model == "quiz" or model == "question":
        return redirect(url_for("quizzes"))
    return redirect(url_for("admin"))
    
if  __name__ == "__main__":
    app.run(debug=True)