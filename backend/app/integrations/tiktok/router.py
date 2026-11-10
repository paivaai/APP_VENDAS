from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import httpx, os
from app.database import get_db
from app.models import TikTokAccount
from app.auth.router import get_current_user

router = APIRouter()

APP_KEY = os.getenv("TIKTOK_APP_KEY")
APP_SECRET = os.getenv("TIKTOK_APP_SECRET")
REDIRECT_URI = os.getenv("TIKTOK_REDIRECT_URI")

@router.get("/connect")
def connect(current_user=Depends(get_current_user)):
    url = (
        f"https://auth.tiktok-shops.com/oauth/authorize"
        f"?app_key={APP_KEY}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&state={current_user.id}"
    )
    return {"auth_url": url}

# LOGIN_SOCIAL: entrar no app usando a conta do TikTok Shop
APP_URL = os.getenv("APP_URL", "https://paivaai.github.io/APP_VENDAS/")

@router.get("/login")
def login_tiktok():
    url = (
        "https://auth.tiktok-shops.com/oauth/authorize"
        f"?app_key={APP_KEY}&redirect_uri={REDIRECT_URI}&state=login"
    )
    return RedirectResponse(url=url)

def _usuario_da_loja(db, shop_id):
    from app.models import User
    email = f"tiktok-{shop_id}@login.pdp.local"
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email, hashed_password="!sem-senha")
        db.add(user); db.commit(); db.refresh(user)
    return user

@router.get("/link")
def link_tiktok(current_user=Depends(get_current_user)):
    url = (
        "https://auth.tiktok-shops.com/oauth/authorize"
        f"?app_key={APP_KEY}&redirect_uri={REDIRECT_URI}&state=app:{current_user.id}"
    )
    return {"auth_url": url}

@router.get("/callback")
async def callback(code: str, state: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://auth.tiktok-shops.com/api/v2/token/get",
            params={
                "app_key": APP_KEY,
                "app_secret": APP_SECRET,
                "auth_code": code,
                "grant_type": "authorized_code",
            }
        )

    print(f"Status: {resp.status_code} | Body: {resp.text[:300]}")

    try:
        data = resp.json()
    except Exception as e:
        return HTMLResponse(f"<h2>Erro JSON</h2><pre>{resp.status_code}: {resp.text[:500]}</pre>")

    if data.get("code") != 0:
        return HTMLResponse(
            f"<h2>TikTok OAuth error {data.get('code')}</h2>"
            f"<pre>{data}</pre>"
            f"<br><a href='https://pdp.paivaai.com.br/dashboard'>Voltar ao dashboard</a>"
        )

    result = data["data"]
    shops = result.get("authorized_shops", [])
    shop_id = shops[0]["shop_id"] if shops else result.get("open_id", "")
    shop_name = shops[0]["shop_name"] if shops else ""

    login_mode = state == "login"
    app_mode = state.startswith("app:")  # LINK_SOCIAL
    if app_mode:
        state = state[4:]
    if login_mode:
        state = _usuario_da_loja(db, shop_id).id
    account = db.query(TikTokAccount).filter(
        TikTokAccount.user_id == state,
        TikTokAccount.shop_id == shop_id
    ).first()

    if not account:
        account = TikTokAccount(user_id=state)

    account.shop_id = shop_id
    account.shop_name = shop_name
    account.access_token = result["access_token"]
    account.refresh_token = result["refresh_token"]
    account.token_expires_at = datetime.utcnow() + timedelta(seconds=result["access_token_expire_in"])

    db.add(account)
    db.commit()
    db.refresh(account)

    background_tasks.add_task(run_import_background, account.id)

    if app_mode:
        return RedirectResponse(url=APP_URL + "#conectado=tiktok")
    if login_mode:
        from app.auth.router import create_token
        from app.models import User
        u = db.query(User).filter(User.id == state).first()
        return RedirectResponse(url=APP_URL + "#token=" + create_token({"sub": u.email}))
    return RedirectResponse(url="https://pdp.paivaai.com.br/dashboard?connected=true")

async def run_import_background(account_id: str):
    from app.database import SessionLocal
    from app.integrations.tiktok.importer import run_full_import
    db = SessionLocal()
    try:
        result = await run_full_import(account_id, db)
        print(f"Importação automática: {result}")
    finally:
        db.close()

@router.get("/accounts")
def list_accounts(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    accounts = db.query(TikTokAccount).filter(TikTokAccount.user_id == current_user.id).all()
    return [{"id": a.id, "shop_id": a.shop_id, "shop_name": a.shop_name} for a in accounts]

@router.post("/sync")
async def sync(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    accounts = db.query(TikTokAccount).filter(TikTokAccount.user_id == current_user.id).all()
    if not accounts:
        raise HTTPException(status_code=400, detail="Nenhuma conta TikTok conectada")
    from app.integrations.tiktok.importer import run_full_import
    results = []
    for account in accounts:
        result = await run_full_import(account.id, db)
        results.append(result)
    return {"synced": len(results), "results": results}
