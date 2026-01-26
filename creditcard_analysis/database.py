import os 
import pymysql 
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.engine import URL 

load_dotenv()

username = os.getenv("MYSQL_USER")
password = os.getenv("MYSQL_PASSWORD")
host     = os.getenv("MYSQL_HOST")
port     = int(os.getenv("MYSQL_PORT"))
database = os.getenv("MYSQL_DB")

url = URL.create(
    "mysql+pymysql",
    username = username,
    password = password,
    host     = host,
    port     = port,
    query    = {"charset": "utf8mb4"}
)

def create_database_if_not_exist():
    with pymysql.connect(user = username, password = password, 
                         host = host, port = port, autocommit = True) as con:
        with con.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database}`")

db_url = URL.create(
    "mysql+pymysql",
    username = username,
    password = password,
    host     = host,
    port     = port,
    database = database,
    query    = {"charset": "utf8mb4"}
)

create_database_if_not_exist()

engine = create_engine(
    db_url,
    pool_size     = 5,
    max_overflow  = 10,
    pool_timeout  = 30,
    pool_recycle  = 3600,
    pool_pre_ping = True,
    future        = True,
    echo          = False
)



SessionLocal = sessionmaker(bind = engine, autoflush = False, autocommit = False, expire_on_commit = False)

Base = declarative_base()

def init_db():
    Base.metadata.create_all(engine)