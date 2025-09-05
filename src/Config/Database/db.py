import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from src.Utils.path import resourcePath

env_path = resourcePath('.env')
print(f"[DEBUG] Tentando carregar .env de: {env_path}")

if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path, override=True)
else:
    print(f"[WARNING] .env não encontrado {env_path}.")

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
    try:
        return SessionLocal()
    except Exception as e:
        print(f"[ERROR] Erro ao criar sessão do banco: {e}")
        raise