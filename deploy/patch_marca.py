"""Liga o retorno para o app da marca (white-label). Uso na VPS: python3 patch_marca.py /opt/pdp/backend
Copia app/marca.py do repositório e inclui rota + middleware no main.py. Idempotente."""
import sys, os, shutil
raiz = sys.argv[1]
aqui = os.path.dirname(os.path.abspath(__file__))
shutil.copy(os.path.join(aqui, "..", "backend", "app", "marca.py"), os.path.join(raiz, "app", "marca.py"))
m = os.path.join(raiz, "app", "main.py")
s = open(m, encoding="utf-8").read()
if "marca_router" not in s:
    shutil.copy(m, m + ".bak8")
    s = s.replace("from app.auth.signup import router as signup_router  # LINK_SOCIAL",
                  "from app.auth.signup import router as signup_router  # LINK_SOCIAL\nfrom app.marca import router as marca_router, marca_middleware", 1)
    s = s.replace('app.include_router(signup_router, prefix="/auth", tags=["auth"])',
                  'app.include_router(signup_router, prefix="/auth", tags=["auth"])\napp.include_router(marca_router, prefix="/auth", tags=["auth"])\napp.middleware("http")(marca_middleware)', 1)
    assert "marca_router, prefix" in s
    open(m, "w", encoding="utf-8").write(s)
print("aplicado")
