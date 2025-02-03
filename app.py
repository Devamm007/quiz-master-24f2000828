from flask import Flask, render_template

app = Flask(__name__)

# CONFIG
from dotenv import load_dotenv
import os

load_dotenv()

# config is a dictionary inside Flask
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS')

import models.models as models

# ROUTES
@app.route('/')
def main():
    return render_template('index.html')


if  __name__ == "__main__":
    app.run(debug=True)