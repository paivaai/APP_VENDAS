"""Criptografia dos tokens OAuth no banco + "Entrar com Google".

Uso na VPS:  python3 patch_crypto_google.py /opt/pdp/backend
Idempotente. Backup .bak4. Não imprime nem grava segredos.

- tokens do TikTok e do Mercado Livre passam a ser gravados criptografados (Fernet, chave TOKEN_ENC_KEY no .env);
  valores antigos em texto puro continuam sendo lidos e são regravados criptografados pelo script reencriptar.py.
- POST /auth/google {credential}: valida o ID token do Google (GOOGLE_CLIENT_ID no .env) e entra/cria a conta.
"""
import sys, os, shutil

raiz = sys.argv[1]
app = os.path.join(raiz, "app")

CRYPTO = '''"""Colunas criptografadas (Fernet). Sem TOKEN_ENC_KEY no ambiente, grava em texto puro (compatível)."""
import os, sys
from sqlalchemy.types import TypeDecorator, Text

# bibliotecas instaladas em /app/_vendor (pasta montada), assim sobrevivem a recriar o container
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_vendor"))

try:
    from cryptography.fernet import Fernet, InvalidToken
except Exception:  # biblioteca ausente
    Fernet = None
    InvalidToken = Exception

_PREFIXO = "enc:"


def _fernet():
    chave = os.getenv("TOKEN_ENC_KEY")
    if not chave or Fernet is None:
        return None
    return Fernet(chave.encode())


class EncryptedText(TypeDecorator):
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        f = _fernet()
        if value is None or f is None or str(value).startswith(_PREFIXO):
            return value
        return _PREFIXO + f.encrypt(str(value).encode()).decode()

    def process_result_value(self, value, dialect):
        if value is None or not str(value).startswith(_PREFIXO):
            return value  # texto puro antigo
        f = _fernet()
        if f is None:
            return value
        try:
            return f.decrypt(str(value)[len(_PREFIXO):].encode()).decode()
        except InvalidToken:
            return value
'''
open(os.path.join(app, "crypto_tokens.py"), "w", encoding="utf-8").write(CRYPTO)

REENC = '''"""Regrava em criptografado os tokens que ainda estão em texto puro. Rodar uma vez:
docker exec pdp-backend-1 python /app/reencriptar.py"""
from sqlalchemy import text
from app.database import engine
from app.crypto_tokens import _fernet, _PREFIXO

f = _fernet()
assert f is not None, "TOKEN_ENC_KEY ausente"
total = 0
with engine.begin() as c:
    for tabela, cols in (("tiktok_accounts", ("access_token", "refresh_token")), ("ml_accounts", ("access_token", "refresh_token"))):
        linhas = c.execute(text(f"SELECT id, {', '.join(cols)} FROM {tabela}")).mappings().all()
        for l in linhas:
            for col in cols:
                v = l[col]
                if v and not str(v).startswith(_PREFIXO):
                    c.execute(text(f"UPDATE {tabela} SET {col}=:v WHERE id=:i"), {"v": _PREFIXO + f.encrypt(str(v).encode()).decode(), "i": l["id"]})
                    total += 1
print("campos criptografados:", total)
'''
open(os.path.join(raiz, "reencriptar.py"), "w", encoding="utf-8").write(REENC)

# models.py: colunas do TikTok
m = os.path.join(app, "models.py")
s = open(m, encoding="utf-8").read()
if "EncryptedText" not in s:
    shutil.copy(m, m + ".bak4")
    s = s.replace("from app.database import Base", "from app.database import Base\nfrom app.crypto_tokens import EncryptedText", 1)
    a1 = "access_token = Column(String, nullable=False)"
    a2 = "refresh_token = Column(String)"
    assert a1 in s and a2 in s
    s = s.replace(a1, "access_token = Column(EncryptedText, nullable=False)", 1)
    s = s.replace(a2, "refresh_token = Column(EncryptedText)", 1)
    open(m, "w", encoding="utf-8").write(s)

# Mercado Livre
ml = os.path.join(app, "integrations", "mercadolivre", "login.py")
t = open(ml, encoding="utf-8").read()
if "EncryptedText" not in t:
    shutil.copy(ml, ml + ".bak4")
    t = t.replace("from app.models import User, gen_uuid", "from app.models import User, gen_uuid\nfrom app.crypto_tokens import EncryptedText", 1)
    for velho, novo in (("access_token = Column(Text)", "access_token = Column(EncryptedText)"), ("refresh_token = Column(Text)", "refresh_token = Column(EncryptedText)")):
        assert velho in t
        t = t.replace(velho, novo, 1)
    open(ml, "w", encoding="utf-8").write(t)

# Google
sg = os.path.join(app, "auth", "signup.py")
g = open(sg, encoding="utf-8").read()
if "GOOGLE_CLIENT_ID" not in g:
    shutil.copy(sg, sg + ".bak4")
    g += '''

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
'''
    open(sg, "w", encoding="utf-8").write(g)

req = os.path.join(raiz, "requirements.txt")
q = open(req, encoding="utf-8").read()
if "cryptography" not in q:
    shutil.copy(req, req + ".bak4")
    open(req, "w", encoding="utf-8").write(q.rstrip("\n") + "\ncryptography>=42\n")
print("aplicado")
