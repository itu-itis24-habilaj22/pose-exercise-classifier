"""The database object shared by the whole backend (SQLAlchemy).

Tables are defined as Python classes in backend/models/ and use `db` from here.
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
