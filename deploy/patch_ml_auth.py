"""Exige login nas rotas /analyze e /ask do Mercado Livre (idempotente)."""
import sys, shutil
c = sys.argv[1]
s = open(c, encoding="utf-8").read()
if "_exigir_login" in s:
    print("já aplicado"); sys.exit(0)
shutil.copy(c, c + ".bak2")
s = s.replace("from fastapi import APIRouter,", "from fastapi import Depends, APIRouter,", 1)
s = s.replace("router = APIRouter()", "from app.auth.router import get_current_user as _exigir_login\nrouter = APIRouter()", 1)
for r in ("/analyze", "/ask"):
    a = '@router.post("%s")' % r
    assert a in s, r
    s = s.replace(a, '@router.post("%s", dependencies=[Depends(_exigir_login)])' % r, 1)
open(c, "w", encoding="utf-8").write(s)
print("aplicado")
