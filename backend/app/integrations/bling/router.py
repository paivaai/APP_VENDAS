
import os

import httpx

import base64

from fastapi import APIRouter, Depends, HTTPException

from fastapi.responses import RedirectResponse

from sqlalchemy.orm import Session

from app.database import get_db

from app.auth.router import get_current_user

router = APIRouter()

BLING_TOKEN_URL = "https://www.bling.com.br/Api/v3/oauth/token"

@router.get("/connect")

def connect(token: str = None, db: Session = Depends(get_db)):

    from jose import jwt

    BLING_CLIENT_ID = os.getenv("BLING_CLIENT_ID")

    user_id = None

    if token:

        try:

            payload = jwt.decode(token, os.getenv("SECRET_KEY", "secret"), algorithms=["HS256"])

            user_id = payload.get("sub")

        except Exception:

            raise HTTPException(status_code=401, detail="Token inválido")

    if not user_id:

        raise HTTPException(status_code=401, detail="Not authenticated")

    

    # user_id aquí é o email (sub do JWT) — buscar ID real no banco

    from app.models import User

    user = db.query(User).filter(User.email == user_id).first()

    if not user:

        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    

    url = (

        f"https://www.bling.com.br/Api/v3/oauth/authorize"

        f"?response_type=code"

        f"&client_id={BLING_CLIENT_ID}"

        f"&state={user.id}"

    )

    return RedirectResponse(url)

@router.get("/callback")

async def callback(code: str, state: str, db: Session = Depends(get_db)):

    BLING_CLIENT_ID = os.getenv("BLING_CLIENT_ID")

    BLING_CLIENT_SECRET = os.getenv("BLING_CLIENT_SECRET")

    BLING_REDIRECT_URI = os.getenv("BLING_REDIRECT_URI")

    credentials = base64.b64encode(

        f"{BLING_CLIENT_ID}:{BLING_CLIENT_SECRET}".encode()

    ).decode()

    async with httpx.AsyncClient() as client:

        response = await client.post(

            BLING_TOKEN_URL,

            headers={

                "Authorization": f"Basic {credentials}",

                "Content-Type": "application/x-www-form-urlencoded",

                "Accept": "application/json"

            },

            data={

                "grant_type": "authorization_code",

                "code": code,

                "redirect_uri": BLING_REDIRECT_URI

            }

        )

    if response.status_code != 200:

        raise HTTPException(status_code=400, detail=f"Erro ao obter token: {response.text}")

    tokens = response.json()

    from app.models import BlingIntegration

    existing = db.query(BlingIntegration).filter(

        BlingIntegration.user_id == state

    ).first()

    if existing:

        existing.access_token = tokens["access_token"]

        existing.refresh_token = tokens.get("refresh_token")

    else:

        integration = BlingIntegration(

            user_id=state,

            access_token=tokens["access_token"],

            refresh_token=tokens.get("refresh_token")

        )

        db.add(integration)

    db.commit()

    return RedirectResponse("https://pdp.paivaai.com.br/dashboard?bling=connected")

@router.get("/products")

async def get_products(current_user=Depends(get_current_user), db: Session = Depends(get_db)):

    from app.models import BlingIntegration

    integration = db.query(BlingIntegration).filter(

        BlingIntegration.user_id == current_user.id

    ).first()

    if not integration:

        raise HTTPException(status_code=404, detail="Bling não conectado")

    async with httpx.AsyncClient() as client:

        response = await client.get(

            "https://www.bling.com.br/Api/v3/produtos",

            headers={"Authorization": f"Bearer {integration.access_token}"}

        )

    return response.json()

@router.get("/orders")

async def get_orders(current_user=Depends(get_current_user), db: Session = Depends(get_db)):

    from app.models import BlingIntegration

    integration = db.query(BlingIntegration).filter(

        BlingIntegration.user_id == current_user.id

    ).first()

    if not integration:

        raise HTTPException(status_code=404, detail="Bling não conectado")

    async with httpx.AsyncClient() as client:

        response = await client.get(

            "https://www.bling.com.br/Api/v3/pedidos/vendas",

            headers={"Authorization": f"Bearer {integration.access_token}"}

        )

    return response.json()

