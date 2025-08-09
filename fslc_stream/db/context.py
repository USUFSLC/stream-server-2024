import flask_sqlalchemy
from fslc_stream.db.models import Base

db = flask_sqlalchemy.SQLAlchemy(model_class=Base)
