"""Avisos urgentes por notificação push (Web Push / VAPID). Versão mínima: pergunta nova de comprador no Mercado Livre.

- GET  /push/chave    chave pública (VAPID) para o app assinar
- POST /push/assinar  guarda a assinatura do aparelho do usuário logado
- POST /push/teste    envia um aviso de teste ao próprio usuário
Um vigia em segundo plano confere as perguntas sem resposta a cada 5 minutos e avisa só as novas.
Não manda dado pessoal do comprador: só o texto da pergunta.
"""
import os, sys, json, time, base64, asyncio, threading, logging
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_vendor"))
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from app.database import engine, SessionLocal
from app.auth.router import get_current_user

log = logging.getLogger(__name__)
router = APIRouter()
PEM = os.getenv("VAPID_PEM", "/app/vapid_private.pem")
APP_URL = os.getenv("APP_URL", "https://paivaai.github.io/APP_VENDAS/")
CLAIM = "https://pdp.paivaai.com.br"
INTERVALO = int(os.getenv("PUSH_INTERVALO", "300"))

with engine.begin() as _c:
    _c.execute(text("CREATE TABLE IF NOT EXISTS push_subs (id SERIAL PRIMARY KEY, user_id VARCHAR NOT NULL, endpoint TEXT UNIQUE NOT NULL, p256dh TEXT NOT NULL, auth TEXT NOT NULL, created_at TIMESTAMP DEFAULT now())"))
    _c.execute(text("CREATE TABLE IF NOT EXISTS push_visto (user_id VARCHAR NOT NULL, chave VARCHAR NOT NULL, PRIMARY KEY (user_id, chave))"))


def _chave_privada():
    if not os.path.exists(PEM):
        k = ec.generate_private_key(ec.SECP256R1())
        with open(PEM, "wb") as f:
            f.write(k.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL, serialization.NoEncryption()))
        os.chmod(PEM, 0o600)
    return serialization.load_pem_private_key(open(PEM, "rb").read(), None)


def _chave_publica():
    pub = _chave_privada().public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    return base64.urlsafe_b64encode(pub).decode().rstrip("=")


_chave_privada()


def _enviar(uid, titulo, corpo):
    from pywebpush import webpush, WebPushException
    with engine.begin() as c:
        subs = c.execute(text("SELECT id, endpoint, p256dh, auth FROM push_subs WHERE user_id=:u"), {"u": uid}).all()
    enviados = 0
    for s in subs:
        try:
            webpush(subscription_info={"endpoint": s[1], "keys": {"p256dh": s[2], "auth": s[3]}},
                    data=json.dumps({"title": titulo, "body": corpo, "url": APP_URL}),
                    vapid_private_key=PEM, vapid_claims={"sub": CLAIM}, ttl=3600)
            enviados += 1
        except WebPushException as e:
            code = getattr(getattr(e, "response", None), "status_code", None)
            if code in (404, 410):
                with engine.begin() as c:
                    c.execute(text("DELETE FROM push_subs WHERE id=:i"), {"i": s[0]})
            else:
                log.error("push falhou (%s): %s", code, e)
        except Exception as e:
            log.error("push falhou: %s", e)
    return enviados


class Assinatura(BaseModel):
    endpoint: str
    p256dh: str
    auth: str


@router.get("/chave")
def chave():
    return {"key": _chave_publica()}


@router.post("/assinar")
def assinar(a: Assinatura, current_user=Depends(get_current_user)):
    with engine.begin() as c:
        c.execute(text("INSERT INTO push_subs (user_id, endpoint, p256dh, auth) VALUES (:u,:e,:p,:a) "
                       "ON CONFLICT (endpoint) DO UPDATE SET user_id=:u, p256dh=:p, auth=:a"),
                  {"u": current_user.id, "e": a.endpoint, "p": a.p256dh, "a": a.auth})
    return {"ok": True}


@router.post("/teste")
def teste(current_user=Depends(get_current_user)):
    n = _enviar(current_user.id, "P-Vendas: aviso de teste", "Tudo certo. Os avisos urgentes da sua loja chegam aqui.")
    if not n:
        raise HTTPException(status_code=404, detail="Nenhum aparelho ativado. Toque em Ativar avisos.")
    return {"enviados": n}


async def _ciclo():
    import httpx
    from app.integrations.mercadolivre.login import MLAccount, _token_valido, API
    db = SessionLocal()
    try:
        uids = [r[0] for r in db.execute(text("SELECT DISTINCT user_id FROM push_subs")).all()]
        for uid in uids:
            accs = db.query(MLAccount).filter(MLAccount.user_id == uid).all()
            if not accs:
                continue
            primeira = db.execute(text("INSERT INTO push_visto (user_id, chave) VALUES (:u,'__semente__') ON CONFLICT DO NOTHING RETURNING 1"), {"u": uid}).first() is not None
            db.commit()
            for acc in accs:
                try:
                    tok = await _token_valido(db, acc)
                    async with httpx.AsyncClient() as c:
                        r = await c.get(API + "/questions/search", headers={"Authorization": "Bearer " + tok}, timeout=30.0, params={
                            "seller_id": acc.ml_user_id, "status": "UNANSWERED", "sort_fields": "date_created", "sort_types": "DESC", "limit": 20})
                except Exception as e:
                    log.error("vigia: %s", e)
                    continue
                if r.status_code != 200:
                    continue
                for q in r.json().get("questions", []):
                    novo = db.execute(text("INSERT INTO push_visto (user_id, chave) VALUES (:u,:k) ON CONFLICT DO NOTHING RETURNING 1"),
                                      {"u": uid, "k": "q" + str(q.get("id"))}).first() is not None
                    db.commit()
                    if novo and not primeira:
                        loja = (" (" + acc.nickname + ")") if len(accs) > 1 and acc.nickname else ""
                        _enviar(uid, "Nova pergunta de comprador" + loja, (q.get("text") or "")[:110] + " Responda rápido para vender.")
    finally:
        db.close()


def _vigia():
    time.sleep(30)
    while True:
        try:
            asyncio.run(_ciclo())
        except Exception as e:
            log.error("vigia: %s", e)
        time.sleep(INTERVALO)


threading.Thread(target=_vigia, daemon=True, name="push-vigia").start()
