from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_bcrypt import Bcrypt
from flask_login import UserMixin

db = SQLAlchemy()
bcrypt = Bcrypt()

'''
Do implement CheckConstraint at end to ensure data integrity with multi-layered data validation.
Ensures database-level enforcement and consistency (as a databse maybe accessed by different application or services),
more performance as database is optimised accordingly,
reduced bypass risk, because chance of multiple entry points to this database,
So implement data validation in frontend, application level, database level, and even API level (If I am left with time to build APIs)
'''

class Registrations(UserMixin, db.Model): #default __tablename__ = "registrations"
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(32), nullable=True)
    username = db.Column(db.String(32), unique=True)
    email = db.Column(db.String(32), nullable=False)
    dob = db.Column(db.Date, nullable=True)
    passhash = db.Column(db.String(256), nullable=False)
    pursuing = db.Column(db.String(32), nullable=True)
    is_admin = db.Column(db.Boolean, nullable = False, default = False)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.passhash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.passhash, password)

    scores = db.relationship('Scores', backref='user', lazy=True, cascade="all, delete-orphan")
    user_inputs = db.relationship('UserInput', backref='user', lazy=True, cascade="all, delete-orphan")

class Subjects(db.Model): #default __tablename__ = "subjects"
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(64), nullable=False)
    subject_des = db.Column(db.String(250), nullable=True)

    chapters = db.relationship('Chapters', backref='subject', lazy=True, cascade="all, delete-orphan")
    quizzes = db.relationship('Quizzes', backref='subject', lazy=True, cascade="all, delete-orphan")

class Chapters(db.Model): #default __tablename__ = "chapters"
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), index=True)
    chapter = db.Column(db.String(64), nullable=False)
    chapter_des = db.Column(db.String(250), nullable=True)

    quizzes = db.relationship('Quizzes', backref='chapter', lazy=True, cascade="all, delete-orphan")

class Quizzes(db.Model): #default __tablename__ = "quizzes"
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), index=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapters.id'), index=True)
    title = db.Column(db.String(64), nullable=False)
    doa = db.Column(db.DateTime)
    time = db.Column(db.Integer, nullable=False)
    remarks = db.Column(db.String(250), nullable=True)
    is_hidden = db.Column(db.Boolean, nullable=False, default=True)

    questions = db.relationship('Questions', backref='quiz', lazy=True, cascade="all, delete-orphan")
    scores = db.relationship('Scores', backref='quiz', lazy=True, cascade="all, delete-orphan")
    user_inputs = db.relationship('UserInput', backref='quiz', lazy=True, cascade="all, delete-orphan")

class Questions(db.Model): #default __tablename__ = "questions"
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), index=True)
    question = db.Column(db.String(300), nullable=False)
    title = db.Column(db.String(64), nullable=False)
    question_type = db.Column(db.String(32), nullable=False)
    option1 = db.Column(db.String(64), nullable=True)
    option2 = db.Column(db.String(64), nullable=True)
    option3 = db.Column(db.String(64), nullable=True)
    option4 = db.Column(db.String(64), nullable=True)
    numeric = db.Column(db.String(20), nullable=True)
    answer = db.Column(db.String(64), nullable=False)
    weightage = db.Column(db.Integer, nullable=False)
    
    user_inputs = db.relationship('UserInput', backref='question', lazy=True)

class UserInput(db.Model): #default __tablename__ = "user_input"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('registrations.id'), index=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), index=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), index=True)
    attempt_number = db.Column(db.Integer, nullable=False)
    input_answer = db.Column(db.String(64), nullable=True)

class Scores(db.Model): #default __tablename__ = "scores"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('registrations.id'), index=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), index=True)
    attempt_number = db.Column(db.Integer, nullable=False)
    start_time = db.Column(db.DateTime, server_default=db.func.now())
    score = db.Column(db.Integer)
    __table_args__ = (db.UniqueConstraint('user_id', 'quiz_id', 'attempt_number', name='quiz_attempt'),)