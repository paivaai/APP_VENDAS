import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Lê o ambiente dentro da função: os.getenv no import já retornou None antes.
def _url() -> str:
    return os.getenv("DATABASE_URL", "")

engine = create_engine(_url(), pool_pre_ping=True) if _url() else None
SessionLocal = sessionmaker(bind=engine, autoflush=False) if engine else None
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
