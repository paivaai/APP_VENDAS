"""OAuth do Bling (usado para conectar a Shopee).

Atenção: o app Bling precisa estar homologado (ou o cliente cadastrado como
usuário de teste) — em "Em desenvolvimento" só o dono consegue autorizar.
"""
import os
import base64
from datetime import datetime, timedelta
import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.utils import decode_email
from app.models import User, BlingIntegration

router = APIRouter()

BLING_AUTH_URL = "https://www.bling.com.br/Api/v3/oauth/authorize"
BLING_TOKEN_URL = "https://www.bling.com.br/Api/v3/oauth/token"


@router.get("/connect")
def connect(token: str = None, db: Session = Depends(get_db)):
    # os.getenv DENTRO da função (no import voltava None)
    client_id = os.getenv("BLING_CLIENT_ID")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = db.query(User).filter(User.email == decode_email(token)).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
    # state = UUID real do usuário (o sub do JWT é e-mail)
    url = f"{BLING_AUTH_URL}?response_type=code&client_id={client_id}&state={user.id}"
    return RedirectResponse(url)


@router.get("/callback")
async def callback(code: str, state: str, db: Session = Depends(get_db)):
    client_id = os.getenv("BLING_CLIENT_ID")
    client_secret = os.getenv("BLING_CLIENT_SECRET")
    redirect_uri = os.getenv("BLING_REDIRECT_URI")
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            BLING_TOKEN_URL,
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            },
            data={"grant_type": "authorization_code", "code": code, "redirect_uri": redirect_uri},
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=400, detail=f"Erro ao obter token: {resp.text}")
    tokens = resp.json()
    expires = datetime.utcnow() + timedelta(seconds=int(tokens.get("expires_in", 21600)))

    row = db.query(BlingIntegration).filter(BlingIntegration.user_id == state).first()
    if row:
        row.access_token = tokens["access_token"]
        row.refresh_token = tokens["refresh_token"]
        row.expires_at = expires
    else:
        db.add(BlingIntegration(
            user_id=state,
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            expires_at=expires,
        ))
    db.commit()
    return RedirectResponse("https://pdp.paivaai.com.br/dashboard?bling=ok")

# TODO: /products, /orders, refresh de token (refresh_token grant) — recuperar da VPS.
