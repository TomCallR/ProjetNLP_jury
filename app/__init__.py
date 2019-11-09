# import os

from flask import Flask
from sqlalchemy import create_engine

import pymysql


app = Flask(import_name=__name__)
# different engines for different databases
# engine = create_engine('sqlite:///:memory:', echo=True)
# basedir = os.path.abspath(os.path.dirname(__file__))
# engine = create_engine('sqlite:///' + os.path.join(basedir, 'projetnlp.db'), echo=True)
engine = create_engine('mysql+pymysql://userx:passwordx@hostx:portx/dbx?charset=utf8mb4')
