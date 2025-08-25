import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
env_path = os.path.join(raiz, '.env')
load_dotenv(dotenv_path=env_path, override=True)

DB_HOST = os.getenv("HOST")
DB_USER = os.getenv("USUARIO")
DB_PASS = os.getenv("SENHA")
DB_NAME = os.getenv("BANCO")
DB_PORT = os.getenv("PORT", "3306")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def getSession():
    return SessionLocal()