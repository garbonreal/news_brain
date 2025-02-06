from sqlalchemy import DateTime, text
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
import os
import pymysql
from dotenv import load_dotenv


db = SQLAlchemy()

load_dotenv(override=False)

MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = int(os.getenv("MYSQL_PORT"))
MYSQL_DB = os.getenv("MYSQL_DATABASE")

print(MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_PORT, MYSQL_DB)

DATABASE_URI = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?charset=utf8mb4"

conn = pymysql.connect(host=MYSQL_HOST,
                       port=MYSQL_PORT,
                       user=MYSQL_USER,
                       passwd=MYSQL_PASSWORD,
                       db=MYSQL_DB,
                       charset='utf8mb4')

engine = create_engine(DATABASE_URI,
                       poolclass=QueuePool,
                       pool_size=10,
                       max_overflow=10,
                       pool_recycle=3600,
                       pool_pre_ping=True, )


class Base(db.Model):
    """base class of all table model"""
    __abstract__ = True
