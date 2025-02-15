from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
# from bcrypt import hashpw, gensalt, checkpw
from functools import wraps

app = Flask(__name__)

# CONFIG: config.py (For this we installed python-dotenv in our venv)
from dotenv import load_dotenv
from os import getenv

load_dotenv()

# config is a dictionary inside Flask
app.config['SECRET_KEY'] = getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = getenv('SQLALCHEMY_TRACK_MODIFICATIONS')

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

def admin_auth(func):
    @wraps(func)
    def auth(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please login to continue", "error")
            return redirect(url_for("login"))
        user = Registrations.query.get(session["user_id"])
        if not user.is_admin:
            flash("You are not authorized!", "error")
            return redirect(url_for("home"))
        return func(*args, **kwargs)
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
    
    # if not checkpw(password.encode('utf-8'), user.passhash):
    if not user.check_password(password):
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
@authentication
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
    dob = datetime.strptime(request.form.get("dob"), '%Y-%m-%d').date()
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
    
    # salt = gensalt()
    # password_hash = hashpw(password.encode('utf-8'), salt)

    email_check = Registrations.query.filter_by(email=email).first()

    if email_check:
        flash("Email already registered. Please use a different email.", "error")
        return redirect(url_for("registration"))

    new_user = Registrations(fullname=fullname, username=username, email=email, dob=dob, password=password, pursuing=pursuing) # passhash=password_hash, pursuing=pursuing)
    db.session.add(new_user) # no need to worry about starting/ending the session, as we are using ORM of SQLAlchemy and not SQL Query
    db.session.commit()
    return redirect(url_for("login"))

@app.route("/profile/delete", methods=["POST"])
@authentication
def delete_account():
    user = Registrations.query.get(session['user_id'])
    if user.is_admin:
        flash("Admin's account cannot be deleted", "error")
        return redirect(url_for("profile"))
    if user:
        db.session.delete(user)
        db.session.commit()
        
        # Clear the session
        session.clear()
        
        flash("Your account has been successfully deleted.", "success")
        return redirect(url_for("login"))
    else:
        flash("User not found.", "error")
        return redirect(url_for("profile"))

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
    # if not checkpw(curr_password.encode("utf-8"), user.passhash)
    if not user.check_password(curr_password):
        flash("Incorrect password!", "error")
        return redirect(url_for("profile"))
    
    if username != user.username:
        new_username = Registrations.query.filter_by(username=username).first()
        if new_username:
            flash("Username already exists!", "error")
            return redirect(url_for("profile"))
        
    # salt = gensalt()
    # new_passhash = hashpw(password.encode("utf-8"), salt)
    user.username = username
    user.password = password
    db.session.commit()
    return redirect(url_for("profile"))

@app.route("/admin")
@admin_auth
def admin():
    user=Registrations.query.get(session['user_id'])
    subjects=Subjects.query.all()
    chapters=Chapters.query.all()
    return render_template('admin.html', user=user, subjects=subjects, chapters=chapters,)

@app.route("/users")
@admin_auth
def users():
    user=Registrations.query.get(session['user_id'])
    users = Registrations.query.filter_by(is_admin=False).all()
    return render_template("users_detail.html", users=users, user=user)

#SUBJECT
@app.route("/admin", methods=["POST"])
@admin_auth
def add_subject():
    subject = request.form.get("subject")
    subject_des = request.form.get("subject_des")

    old_subject = Subjects.query.filter_by(subject=subject).first()

    if old_subject:
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
    subject = request.form.get("subject")
    subject_des = request.form.get("subject_des")

    old_subject = Subjects.query.get(id)

    if old_subject!=subject and subject:
        new_subject = Subjects.query.filter_by(subject=subject).first()
        if new_subject:
            flash("Subject already exist!", "error")
            return redirect(url_for("admin"))

    if not subject:
        subject=old_subject.subject
    if not subject_des:
        subject_des=old_subject.subject_des
        
    old_subject.subject = subject
    old_subject.subject_des = subject_des
    db.session.commit()
    flash("Subject updated successfully!", "success")
    return redirect(url_for("admin"))

@app.route("/admin/subject/<int:id>/delete", methods=["POST"])
@admin_auth
def del_subject(id):
    subject = Subjects.query.get(id)
    db.session.delete(subject)
    db.session.commit()
    flash("Subject deleted successfully!", "success")
    return redirect(url_for("admin"))

#CHAPTER
@app.route("/admin/subject/<int:id>/add_chapter", methods=["POST"])
@admin_auth
def add_chapter(id):
    if not id:
        return redirect(url_for("admin"))

    chapter = request.form.get("chapter")
    chapter_des = request.form.get("chapter_des")
    old_chapter = Chapters.query.filter_by(chapter=chapter).first()

    if old_chapter:
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
    chapter = request.form.get("chapter")
    chapter_des = request.form.get("chapter_des")

    old_chapter = Chapters.query.get(id)

    if old_chapter!=chapter and chapter:
        new_chapter = Chapters.query.filter_by(chapter=chapter)
        if new_chapter:
            flash("Chapter already exist!", "error")
            return redirect(url_for("admin"))

    if not chapter:
        chapter=old_chapter.chapter
    if not chapter_des:
        chapter_des=old_chapter.chapter_des
        
    old_chapter.chapter = chapter
    old_chapter.chapter_des = chapter_des
    db.session.commit()
    flash("Chapter updated successfully!", "success")
    return redirect(url_for("admin"))

@app.route("/admin/chapter/<int:id>/delete", methods=["POST"])
@admin_auth
def del_chapter(id):
    chapter = Chapters.query.get(id)
    db.session.delete(chapter)
    db.session.commit()
    flash("Chapter deleted successfully!", "success")
    return redirect(url_for("admin"))

#QUIZ
@app.route("/admin/quizzes")
@admin_auth
def quizzes():
    user=Registrations.query.get(session['user_id'])
    quizzes=Quizzes.query.all()
    questions=Questions.query.all()
    return render_template("quizzes.html", user=user, quizzes=quizzes, questions=questions)

@app.route("/admin/quizzes/add", methods=["POST"])
@admin_auth
def add_quiz():
    chap_id = request.form.get("chap_id")
    title = request.form.get("title")
    doa = datetime.strptime(request.form.get("doa"), '%Y-%m-%d').date()
    time = request.form.get("time")
    remarks = request.form.get("remarks")

    chapter = Chapters.query.get(chap_id)

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
    title = request.form.get("title")
    doa = request.form.get("doa")
    if doa != "":
        doa = datetime.strptime(request.form.get("doa"), '%Y-%m-%d').date()
    time = request.form.get("time")
    remarks = request.form.get("remarks")

    old_quiz = Quizzes.query.get(id)

    if not title:
        title = old_quiz.title
    if not doa:
        doa = old_quiz.doa
    if not time:
        time = old_quiz.time
    if not remarks:
        remarks = old_quiz.remarks
    
    old_quiz.title = title
    old_quiz.doa = doa
    old_quiz.time = time
    old_quiz.remarks = remarks
    db.session.commit()
    flash("Quiz updated succesfully!", "success")
    return redirect(url_for("quizzes"))

@app.route("/admin/quizzes/<int:id>/delete", methods=["POST"])
@admin_auth
def del_quiz(id):
    quiz = Quizzes.query.get(id)
    db.session.delete(quiz)
    db.session.commit()
    flash("Quiz deleted successfully!", "success")
    return redirect(url_for("quizzes"))

#QUESTION
@app.route("/admin/quizzes/<int:id>/question/add", methods=["POST"])
@admin_auth
def add_question(id):
    # Only for single correct, did not implement multiple correct or numeric.
    question_type = request.form.get("question_type")
    question = request.form.get("question")
    title = request.form.get("title")
    option1 = request.form.get("option1")
    option2 = request.form.get("option2")
    option3 = request.form.get("option3")
    option4 = request.form.get("option4")
    answer = request.form.get("answer")
    weightage = int(request.form.get("weightage"))

    if not question:
        flash("Enter question statement", "error")
        return redirect(url_for("quizzes"))
    
    if not title:
        flash("Enter title of the question", "error")
        return redirect(url_for("quizzes"))

    if not weightage or weightage==0 or weightage<0 or weightage>10:
        flash("Give valid weightage to question from 1-10 points", "error")
        return redirect(url_for("quizzes"))

    if not option1 or not option2 or not option3 or not option4:
        flash("Please fill all the options", "error")
        return redirect(url_for("quizzes"))
    
    if not answer:
        flash("Give valid answer", "error")
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

@app.route("/subject/chapter/quiz/question/<int:id>/edit", methods=["POST"])
@admin_auth
def edit_question(id):
    # Only for single correct, did not implement multiple correct or numeric.
    old_question = Questions.query.get(id)

    if old_question.question_type == "single_correct":
        question = request.form.get("question")
        title = request.form.get("title")
        option1 = request.form.get("option1")
        option2 = request.form.get("option2")
        option3 = request.form.get("option3")
        option4 = request.form.get("option4")
        answer = request.form.get("answer")
        if request.form.get("weightage"):
            weightage = int(request.form.get("weightage"))

        if not question:
            question = old_question.question
        if not title:
            title = old_question.title
        if not option1:
            option1 = old_question.option1
        if not option2:
            option2 = old_question.option2
        if not option3:
            option3 = old_question.option3
        if not option4:
            option4 = old_question.option4
        if not answer:
            answer = old_question.answer
        if not request.form.get("weightage"):
            weightage = old_question.weightage
        if weightage==0 or weightage<0 or weightage>10:
            flash("Give valid weightage to question from 1-10 points", "error")
            return redirect(url_for("quizzes"))
        
        old_question.question = question
        old_question.title = title
        old_question.option1 = option1
        old_question.option2 = option2
        old_question.option3 = option3
        old_question.option4 = option4
        old_question.answer = answer
        old_question.weightage = weightage
        db.session.commit()
        flash("Question updated successfully", "success")
        return redirect(url_for("quizzes"))
    elif old_question.question_type == "multi_correct":
        pass
    elif old_question.question_type == "numerical":
        pass

@app.route("/subject/chapter/quiz/question/<int:id>/delete", methods=["POST"])
@admin_auth
def del_question(id):
    question = Questions.query.get(id)
    db.session.delete(question)
    db.session.commit()
    flash("Question deleted successfully!", "success")
    return redirect(url_for("quizzes"))

    
if  __name__ == "__main__":
    app.run(debug=True)