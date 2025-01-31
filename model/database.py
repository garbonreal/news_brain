from sqlalchemy import DateTime, text
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

import pymysql

db = SQLAlchemy()

conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', passwd='110110', db='idea_bank',
                       charset='utf8mb4')
engine = create_engine("mysql+pymysql://root:110110@127.0.0.1:3306/idea_bank?charset=utf8mb4",
                       poolclass=QueuePool,
                       pool_size=10,
                       max_overflow=10,
                       pool_recycle=3600,
                       pool_pre_ping=True, )


class Base(db.Model):
    """base class of all table model"""
    __abstract__ = True
