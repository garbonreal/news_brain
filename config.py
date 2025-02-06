import os
from dotenv import load_dotenv

load_dotenv(override=False)

SECRET_KEY = os.urandom(24)

# configuring the mysql Database
HOSTNAME = os.getenv("MYSQL_HOST")
PORT = os.getenv("MYSQL_PORT")
DATABASE = os.getenv("MYSQL_DATABASE")
USERNAME = os.getenv("MYSQL_USER")
PASSWORD = os.getenv("MYSQL_PASSWORD")

# configure the database connection address
DB_URI = 'mysql+pymysql://' + USERNAME + ':' + PASSWORD + '@' + HOSTNAME \
                                        + ':' + PORT + '/' + DATABASE + "?charset=utf8mb4"
SQLALCHEMY_DATABASE_URI = DB_URI
SQLALCHEMY_TRACK_MODIFICATIONS = True
REDIS_URL = os.getenv("REDIS_URL")
