"""Aplica "Entrar com TikTok" no backend real da VPS (idempotente).

Uso na VPS:  python3 patch_tiktok_login.py /opt/pdp/backend/app/integrations/tiktok/router.py
Não toca em segredos. Faz backup .bak ao lado do arquivo.
"""
import sys, shutil

caminho = sys.argv[1]
src = open(caminho, encoding="utf-8").read()
if "LOGIN_SOCIAL" in src:
    print("já aplicado"); sys.exit(0)
shutil.copy(caminho, caminho + ".bak")

# 1) imports + helper + rota /login (antes do /callback)
antes = '@router.get("/callback")'
novo = '''# LOGIN_SOCIAL: entrar no app usando a conta do TikTok Shop
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

'''
assert antes in src
src = src.replace(antes, novo + antes, 1)

# 2) no callback: se state == "login", troca pelo usuário da loja
marca = '    account = db.query(TikTokAccount).filter('
assert marca in src
src = src.replace(marca, '''    login_mode = state == "login"
    if login_mode:
        state = _usuario_da_loja(db, shop_id).id
''' + marca, 1)

# 3) redirect final: no modo login devolve o JWT para o app (no fragmento da URL)
final = 'return RedirectResponse(url="https://pdp.paivaai.com.br/dashboard?connected=true")'
assert final in src
src = src.replace(final, '''if login_mode:
        from app.auth.router import create_token
        from app.models import User
        u = db.query(User).filter(User.id == state).first()
        return RedirectResponse(url=APP_URL + "#token=" + create_token({"sub": u.email}))
    ''' + final, 1)

open(caminho, "w", encoding="utf-8").write(src)
print("aplicado")
