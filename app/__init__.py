from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config.from_object('config')

db = SQLAlchemy(app)

app.secret_key = 'INSERT YOUR SECRET KEY HERE'
#used for session cookies
#Recommended: in Python interpreter, use os.urandom(24) to produce a random string and use resulting value for key

from app import views, models
