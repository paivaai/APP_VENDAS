"""White-label: depois do login no Mercado Livre/TikTok, volta para o app da marca de onde a pessoa veio.

- GET /auth/marca?r=<slug>&to=<url>  guarda a marca num cookie curto e segue para o endereço de autorização (lista fechada)
- middleware: se a resposta redireciona para o app (APP_URL) e há cookie de marca, troca para APP_URL + c/<slug>/
Sem cookie, nada muda (app principal).
"""
import os, re
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

router = APIRouter()
APP_URL = os.getenv("APP_URL", "https://paivaai.github.io/APP_VENDAS/")
API_URL = os.getenv("API_PUBLIC_URL", "https://api.pdp.paivaai.com.br")
SLUG = re.compile(r"[a-z0-9][a-z0-9-]{0,39}")
PERMITIDOS = (
    API_URL + "/integrations/",
    "https://auth.mercadolivre.com",
    "https://auth.mercadolibre.com",
    "https://auth.tiktok-shops.com/",
)


@router.get("/marca")
def ir_com_marca(r: str, to: str):
    if not SLUG.fullmatch(r):
        raise HTTPException(status_code=400, detail="marca inválida")
    if not any(to.startswith(p) for p in PERMITIDOS):
        raise HTTPException(status_code=400, detail="destino não permitido")
    resp = RedirectResponse(url=to, status_code=302)
    resp.set_cookie("pv_r", r, max_age=900, httponly=True, secure=True, samesite="lax")
    return resp


async def marca_middleware(request, call_next):
    resp = await call_next(request)
    if resp.status_code in (301, 302, 303, 307, 308):
        loc = resp.headers.get("location", "")
        slug = request.cookies.get("pv_r")
        if slug and SLUG.fullmatch(slug) and loc.startswith(APP_URL):
            resp.headers["location"] = APP_URL + "c/" + slug + "/" + loc[len(APP_URL):]
            resp.delete_cookie("pv_r")
    return resp
