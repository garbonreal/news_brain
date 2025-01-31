from .database import db
from .user import User
from .all_report import AllReport
from .website_url import WebsiteUrl
from .report import Report


def init_db(app):
    db.init_app(app)
