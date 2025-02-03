from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from app import app

db = SQLAlchemy(app)

class Registrations(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(32), nullable=True)
    username = db.Column(db.String(32), unique=True)
    email = db.Column(db.String(32), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    passhash = db.Column(db.String(256), nullable=False)
    pursuing = db.Column(db.String(32), nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)

    scores = db.relationship('Scores', backref='user', lazy='True')
    user_inputs = db.relationship('UserInput', backref='user', lazy='True')

class Subjects(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(64), nullable=False)
    subject_des = db.Column(db.String(250), nullable=True)

    chapters = db.relationship('Chapters', backref='subject', lazy='True')
    quizzes = db.relationship('Quizzes', backref='subject', lazy='True')

class Chapters(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), index=True)
    chapter = db.Column(db.String(64), nullable=False)
    chapter_des = db.Column(db.String(250), nullable=True)

    quizzes = db.relationship('Quizzes', backref='chapter', lazy='True')

class Quizzes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), index=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapters.id'), index=True)
    doa = db.Column(db.Date)
    time = db.Column(db.Integer, nullable=False)
    remarks = db.Column(db.String(250), nullable=True)

    questions = db.relationship('Questions', backref='quiz', lazy='True', cascade="all, delete-orphan")
    scores = db.relationship('Scores', backref='quiz', lazy='True')
    user_inputs = db.relationship('UserInput', backref='quiz', lazy='True')

class Questions(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), index=True)
    question = db.Column(db.String(300), nullable=False)
    question_type = db.Column(db.String(32), nullable=False)
    option1 = db.Column(db.String(64), nullable=True)
    option2 = db.Column(db.String(64), nullable=True)
    option3 = db.Column(db.String(64), nullable=True)
    option4 = db.Column(db.String(64), nullable=True)
    numeric = db.Column(db.String(20), nullable=True)
    answer = db.Column(db.String(64), nullable=False)

    user_inputs = db.relationship('UserInput', backref='question', lazy='True')

class UserInput(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('registrations.id'), index=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), index=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), index=True)
    input_answer = db.Column(db.String(64), nullable=True)

class Scores(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('registrations.id'), index=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), index=True)
    attempt_number = db.Column(db.Integer, nullable=False)
    start_time = db.Column(db.DateTime, server_default=db.func.now())
    score = db.Column(db.Integer)
    __table_args__ = (db.UniqueConstraint('user_id', 'quiz_id', 'attempt_number', name='uq_user_quiz_attempt'),)

with app.app_context():
    db.create_all()