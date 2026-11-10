"""Regrava em criptografado os tokens que ainda estão em texto puro. Rodar uma vez:
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
