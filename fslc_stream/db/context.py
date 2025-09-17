import flask_sqlalchemy
import flask_migrate
from fslc_stream.db.models import Base

db = flask_sqlalchemy.SQLAlchemy(model_class=Base)
migrate = flask_migrate.Migrate()
