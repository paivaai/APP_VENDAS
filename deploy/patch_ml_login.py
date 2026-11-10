"""Aplica "Entrar com Mercado Livre" no backend real da VPS (idempotente).

Uso na VPS:  python3 patch_ml_login.py /opt/pdp/backend/app/integrations/mercadolivre
- cria login.py (tabela ml_accounts, rota /login, rota /orders)
- no callback antigo: se state == "login" guarda o token no servidor e devolve o app;
  e deixa de devolver access_token/refresh_token na resposta (vazamento).
"""
import sys, os, shutil

pasta = sys.argv[1]
router = os.path.join(pasta, "router.py")
src = open(router, encoding="utf-8").read()
if "LOGIN_SOCIAL_ML" in src:
    print("já aplicado"); sys.exit(0)
shutil.copy(router, router + ".bak")

LOGIN = '''"""Entrar com Mercado Livre: guarda o token no servidor e entrega só o JWT do app."""
import os, httpx
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.orm import Session
from app.database import Base, engine, SessionLocal, get_db
from app.models import User, gen_uuid
from app.auth.router import create_token, get_current_user
from app.integrations.mercadolivre.oauth import MercadoLivreOAuth

APP_URL = os.getenv("APP_URL", "https://paivaai.github.io/APP_VENDAS/")
API = "https://api.mercadolibre.com"
router = APIRouter()
oauth = MercadoLivreOAuth()


class MLAccount(Base):
    __tablename__ = "ml_accounts"
    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, nullable=False)
    ml_user_id = Column(String, nullable=False, unique=True)
    nickname = Column(String)
    access_token = Column(Text)
    refresh_token = Column(Text)
    token_expires_at = Column(DateTime)


MLAccount.__table__.create(bind=engine, checkfirst=True)


@router.get("/login")
def login_ml():
    return RedirectResponse(url=oauth.get_auth_url("login"))


def finish_login(token_response, user_info):
    db = SessionLocal()
    try:
        uid = str(user_info.get("id"))
        email = f"ml-{uid}@login.pdp.local"
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(email=email, hashed_password="!sem-senha")
            db.add(user); db.commit(); db.refresh(user)
        acc = db.query(MLAccount).filter(MLAccount.ml_user_id == uid).first()
        if not acc:
            acc = MLAccount(user_id=user.id, ml_user_id=uid)
        acc.nickname = user_info.get("nickname")
        acc.access_token = token_response["access_token"]
        acc.refresh_token = token_response.get("refresh_token")
        acc.token_expires_at = datetime.utcnow() + timedelta(seconds=int(token_response.get("expires_in") or 21600))
        db.add(acc); db.commit()
        return RedirectResponse(url=APP_URL + "#token=" + create_token({"sub": email}))
    finally:
        db.close()


async def _token_valido(db, acc):
    if acc.token_expires_at and acc.token_expires_at > datetime.utcnow() + timedelta(seconds=90):
        return acc.access_token
    async with httpx.AsyncClient() as c:
        r = await c.post(API + "/oauth/token", data={
            "grant_type": "refresh_token", "client_id": oauth.app_id,
            "client_secret": oauth.client_secret, "refresh_token": acc.refresh_token}, timeout=30.0)
    if r.status_code != 200:
        raise HTTPException(status_code=502, detail="Mercado Livre recusou renovar a sessão")
    d = r.json()
    acc.access_token = d["access_token"]
    acc.refresh_token = d.get("refresh_token", acc.refresh_token)
    acc.token_expires_at = datetime.utcnow() + timedelta(seconds=int(d.get("expires_in") or 21600))
    db.add(acc); db.commit()
    return acc.access_token


@router.get("/orders")
async def pedidos_ml(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Pedidos do vendedor. Devolve só id, status, valor e data: nunca dados do comprador."""
    acc = db.query(MLAccount).filter(MLAccount.user_id == current_user.id).first()
    if not acc:
        return []
    tok = await _token_valido(db, acc)
    async with httpx.AsyncClient() as c:
        r = await c.get(API + "/orders/search", params={"seller": acc.ml_user_id, "sort": "date_desc", "limit": 50},
                        headers={"Authorization": "Bearer " + tok}, timeout=30.0)
    if r.status_code != 200:
        raise HTTPException(status_code=502, detail="Mercado Livre não respondeu os pedidos")
    return [{"id": str(o.get("id")), "order_id": str(o.get("id")), "status": o.get("status"),
             "total": o.get("total_amount"), "created_at": o.get("date_created"), "channel": "Mercado Livre"}
            for o in r.json().get("results", [])]


@router.get("/me")
def quem_sou_eu(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    acc = db.query(MLAccount).filter(MLAccount.user_id == current_user.id).first()
    return {"connected": bool(acc), "nickname": acc.nickname if acc else None}
'''
open(os.path.join(pasta, "login.py"), "w", encoding="utf-8").write(LOGIN)

# callback: modo login + parar de devolver tokens
ancora = '        user_info = await oauth.get_user_info(token_response["access_token"])\n'
assert ancora in src
src = src.replace(ancora, ancora + '''        if state == "login":  # LOGIN_SOCIAL_ML
            from app.integrations.mercadolivre.login import finish_login
            return finish_login(token_response, user_info)
''', 1)
for linha in ('"access_token": token_response["access_token"],', '"refresh_token": token_response.get("refresh_token"),'):
    assert linha in src
    src = src.replace(linha, "", 1)

src += '''

from app.integrations.mercadolivre.login import router as _login_router  # LOGIN_SOCIAL_ML
router.include_router(_login_router)
'''
open(router, "w", encoding="utf-8").write(src)
print("aplicado")
