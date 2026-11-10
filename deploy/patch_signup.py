"""Cadastro por e-mail (nome, e-mail, senha) + confirmação por e-mail + ligar ML/TikTok a uma conta existente.

Uso na VPS:  python3 patch_signup.py /opt/pdp/backend/app
Idempotente. Faz backup .bak3 dos arquivos que altera. Não toca em segredos.

E-mail de confirmação: variáveis SMTP_HOST, SMTP_PORT (465 ou 587), SMTP_USER, SMTP_PASS, SMTP_FROM no .env.
Sem SMTP configurado, a conta nasce confirmada (modo demonstração) e a resposta avisa "verificacao": "desativada".
"""
import sys, os, shutil

base = sys.argv[1]
auth_dir = os.path.join(base, "auth")

SIGNUP = '''"""Cadastro por e-mail, confirmação e entrada. LINK_SOCIAL"""
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
        f"Olá, {nome}!\\n\\nSeu cadastro no P-Vendas foi criado. Para ativar a conta, abra o link:\\n{link}\\n\\n"
        "Depois é só voltar ao app e entrar com o seu e-mail e a senha.\\n\\nSe não foi você, ignore esta mensagem."
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
    if not nome or not re.match(r"^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$", email) or len(d.password) < 8:
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
'''
open(os.path.join(auth_dir, "signup.py"), "w", encoding="utf-8").write(SIGNUP)

# main.py: inclui o router
main = os.path.join(base, "main.py")
m = open(main, encoding="utf-8").read()
if "LINK_SOCIAL" not in m:
    shutil.copy(main, main + ".bak3")
    m = m.replace("from app.auth.router import router as auth_router",
                  "from app.auth.router import router as auth_router\nfrom app.auth.signup import router as signup_router  # LINK_SOCIAL", 1)
    m = m.replace('app.include_router(auth_router, prefix="/auth", tags=["auth"])',
                  'app.include_router(auth_router, prefix="/auth", tags=["auth"])\napp.include_router(signup_router, prefix="/auth", tags=["auth"])', 1)
    assert "signup_router, prefix" in m
    open(main, "w", encoding="utf-8").write(m)

# Mercado Livre: ligar a uma conta existente
mlp = os.path.join(base, "integrations", "mercadolivre")
ml_login = os.path.join(mlp, "login.py")
t = open(ml_login, encoding="utf-8").read()
if "LINK_SOCIAL" not in t:
    shutil.copy(ml_login, ml_login + ".bak3")
    t += '''

# LINK_SOCIAL: ligar o Mercado Livre a uma conta criada por e-mail
from jose import jwt as _jwt
from app.auth.router import SECRET_KEY as _SK, ALGORITHM as _AL


@router.get("/link")
def link_ml(current_user=Depends(get_current_user)):
    estado = _jwt.encode({"sub": current_user.email, "lk": 1, "exp": datetime.utcnow() + timedelta(minutes=10)}, _SK, algorithm=_AL)
    return {"auth_url": oauth.get_auth_url("link:" + estado)}


def finish_link(state, token_response, user_info):
    try:
        dados = _jwt.decode(state[5:], _SK, algorithms=[_AL])
    except Exception:
        raise HTTPException(status_code=400, detail="Pedido de ligação expirado. Tente de novo pelo app.")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == dados["sub"]).first()
        uid = str(user_info.get("id"))
        acc = db.query(MLAccount).filter(MLAccount.ml_user_id == uid).first() or MLAccount(ml_user_id=uid)
        acc.user_id = user.id
        acc.nickname = user_info.get("nickname")
        acc.access_token = token_response["access_token"]
        acc.refresh_token = token_response.get("refresh_token")
        acc.token_expires_at = datetime.utcnow() + timedelta(seconds=int(token_response.get("expires_in") or 21600))
        db.add(acc); db.commit()
        return RedirectResponse(url=APP_URL + "#conectado=ml")
    finally:
        db.close()
'''
    open(ml_login, "w", encoding="utf-8").write(t)
    ml_router = os.path.join(mlp, "router.py")
    r = open(ml_router, encoding="utf-8").read()
    shutil.copy(ml_router, ml_router + ".bak3")
    alvo = '''            return finish_login(token_response, user_info)\n'''
    assert alvo in r
    r = r.replace(alvo, alvo + '''        if state and state.startswith("link:"):
            from app.integrations.mercadolivre.login import finish_link
            return finish_link(state, token_response, user_info)
''', 1)
    open(ml_router, "w", encoding="utf-8").write(r)

# TikTok: ligar a uma conta existente
tk = os.path.join(base, "integrations", "tiktok", "router.py")
x = open(tk, encoding="utf-8").read()
if "LINK_SOCIAL" not in x:
    shutil.copy(tk, tk + ".bak3")
    ant = '    login_mode = state == "login"\n'
    assert ant in x
    x = x.replace(ant, ant + '    app_mode = state.startswith("app:")  # LINK_SOCIAL\n    if app_mode:\n        state = state[4:]\n', 1)
    fin = '    if login_mode:\n        from app.auth.router import create_token'
    assert fin in x or 'if login_mode:\n        from app.auth.router import create_token' in x
    x = x.replace('if login_mode:\n        from app.auth.router import create_token',
                  'if app_mode:\n        return RedirectResponse(url=APP_URL + "#conectado=tiktok")\n    if login_mode:\n        from app.auth.router import create_token', 1)
    antes = '@router.get("/callback")'
    x = x.replace(antes, '''@router.get("/link")
def link_tiktok(current_user=Depends(get_current_user)):
    url = (
        "https://auth.tiktok-shops.com/oauth/authorize"
        f"?app_key={APP_KEY}&redirect_uri={REDIRECT_URI}&state=app:{current_user.id}"
    )
    return {"auth_url": url}

''' + antes, 1)
    open(tk, "w", encoding="utf-8").write(x)
print("aplicado")
