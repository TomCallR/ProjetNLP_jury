from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from private.privateconfig import Config

app = Flask(import_name=__name__)

app.config.from_object(Config)
db = SQLAlchemy(app)

from app import routes
from app.database import models
