"""Cadastro por e-mail, confirmação e entrada. LINK_SOCIAL"""
import os, re, secrets, smtplib, threading, logging
from email.message import EmailMessage
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import engine, get_db
from app.models import User
from app.auth.router import pwd_context, create_token, get_current_user

log = logging.getLogger(__name__)
router = APIRouter()
APP_URL = os.getenv("APP_URL", "https://paivaai.github.io/APP_VENDAS/")
API_URL = os.getenv("API_PUBLIC_URL", "https://api.pdp.paivaai.com.br")

with engine.begin() as _c:
    _c.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS name VARCHAR"))
    _c.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT TRUE"))
    _c.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS verify_token VARCHAR"))


class Cadastro(BaseModel):
    name: str
    email: str
    password: str


class Entrada(BaseModel):
    email: str
    password: str


def _smtp_ok():
    return all(os.getenv(k) for k in ("SMTP_HOST", "SMTP_USER", "SMTP_PASS"))


def _enviar(para, nome, link):
    msg = EmailMessage()
    msg["Subject"] = "Confirme seu cadastro no P-Vendas"
    msg["From"] = os.getenv("SMTP_FROM") or os.getenv("SMTP_USER")
    msg["To"] = para
    msg.set_content(
        f"Olá, {nome}!\n\nSeu cadastro no P-Vendas foi criado. Para ativar a conta, abra o link:\n{link}\n\n"
        "Depois é só voltar ao app e entrar com o seu e-mail e a senha.\n\nSe não foi você, ignore esta mensagem."
    )
    porta = int(os.getenv("SMTP_PORT", "587"))
    try:
        if porta == 465:
            s = smtplib.SMTP_SSL(os.getenv("SMTP_HOST"), porta, timeout=20)
        else:
            s = smtplib.SMTP(os.getenv("SMTP_HOST"), porta, timeout=20)
            s.starttls()
        s.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASS"))
        s.send_message(msg)
        s.quit()
    except Exception as e:  # nunca derruba o cadastro
        log.error("falha ao enviar e-mail de confirmação: %s", e)


@router.post("/signup")
def signup(d: Cadastro, db: Session = Depends(get_db)):
    email = d.email.strip().lower()
    nome = d.name.strip()[:80]
    if not nome or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email) or len(d.password) < 8:
        raise HTTPException(status_code=422, detail="Preencha nome, e-mail válido e senha com 8 ou mais caracteres")
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Este e-mail já tem cadastro. Use Entrar.")
    user = User(email=email, hashed_password=pwd_context.hash(d.password))
    db.add(user); db.commit(); db.refresh(user)
    if _smtp_ok():
        tok = secrets.token_urlsafe(32)
        db.execute(text("UPDATE users SET name=:n, email_verified=FALSE, verify_token=:t WHERE id=:i"), {"n": nome, "t": tok, "i": user.id})
        db.commit()
        threading.Thread(target=_enviar, args=(email, nome, f"{API_URL}/auth/verify?token={tok}"), daemon=True).start()
        return {"ok": True, "verificacao": "email"}
    db.execute(text("UPDATE users SET name=:n, email_verified=TRUE WHERE id=:i"), {"n": nome, "i": user.id})
    db.commit()
    return {"ok": True, "verificacao": "desativada", "access_token": create_token({"sub": email}), "name": nome}


@router.get("/verify")
def verify(token: str, db: Session = Depends(get_db)):
    r = db.execute(text("UPDATE users SET email_verified=TRUE, verify_token=NULL WHERE verify_token=:t RETURNING id"), {"t": token}).first()
    db.commit()
    return RedirectResponse(url=APP_URL + ("#verificado=1" if r else "#verificado=0"))


@router.post("/entrar")
def entrar(d: Entrada, db: Session = Depends(get_db)):
    email = d.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    ok = False
    if user:
        try:
            ok = pwd_context.verify(d.password, user.hashed_password)
        except Exception:
            ok = False
    if not ok:
        raise HTTPException(status_code=401, detail="E-mail ou senha incorretos")
    row = db.execute(text("SELECT name, email_verified FROM users WHERE id=:i"), {"i": user.id}).first()
    if row and row[1] is False:
        raise HTTPException(status_code=403, detail="Confirme seu e-mail antes de entrar. Procure a mensagem do P-Vendas.")
    return {"access_token": create_token({"sub": email}), "name": row[0] if row else None}


@router.get("/perfil")
def perfil(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    row = db.execute(text("SELECT name FROM users WHERE id=:i"), {"i": current_user.id}).first()
    return {"name": row[0] if row else None}


# GOOGLE_CLIENT_ID: entrar com a conta Google
class GoogleEntrada(BaseModel):
    credential: str


@router.post("/google")
def entrar_google(d: GoogleEntrada, db: Session = Depends(get_db)):
    import httpx
    cid = os.getenv("GOOGLE_CLIENT_ID")
    if not cid:
        raise HTTPException(status_code=503, detail="Entrada com Google ainda não configurada")
    try:
        r = httpx.get("https://oauth2.googleapis.com/tokeninfo", params={"id_token": d.credential}, timeout=15)
        info = r.json()
    except Exception:
        raise HTTPException(status_code=502, detail="Não foi possível validar com o Google")
    if r.status_code != 200 or info.get("aud") != cid or str(info.get("email_verified")).lower() != "true":
        raise HTTPException(status_code=401, detail="Conta Google não validada")
    email = str(info.get("email", "")).lower()
    nome = (info.get("name") or email.split("@")[0])[:80]
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email, hashed_password="!google")
        db.add(user); db.commit(); db.refresh(user)
    db.execute(text("UPDATE users SET name=COALESCE(name, :n), email_verified=TRUE WHERE id=:i"), {"n": nome, "i": user.id})
    db.commit()
    return {"access_token": create_token({"sub": email}), "name": nome}
