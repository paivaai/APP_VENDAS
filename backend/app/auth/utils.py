"""Auth mínima. O `sub` do JWT é o E-MAIL (não o id do usuário): quem precisar
do UUID deve consultar a tabela users pelo e-mail.
TODO: reconciliar com o módulo de auth real da VPS (register/login/hash).
"""
import os
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def create_token(email: str) -> str:
    hours = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", "24"))
    payload = {"sub": email, "exp": datetime.utcnow() + timedelta(hours=hours)}
    return jwt.encode(payload, os.getenv("SECRET_KEY", ""), algorithm="HS256")


def decode_email(token: str) -> str:
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY", ""), algorithms=["HS256"])
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")
    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=401, detail="Token inválido")
    return email


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = db.query(User).filter(User.email == decode_email(token)).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
    return user
