from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# from flask_bootstrap import Bootstrap
from private.privateconfig import Config

app = Flask(import_name=__name__, static_url_path="/static")

# Bootstrap(app)
app.config.from_object(Config)
db = SQLAlchemy(app)

from app import routes
from app.database import models
