"""Liga os avisos urgentes (push). Uso na VPS: python3 patch_push.py /opt/pdp/backend
Copia app/push.py do repositório e inclui a rota no main.py. Idempotente. Requer pywebpush em /app/_vendor."""
import sys, os, shutil
raiz = sys.argv[1]
aqui = os.path.dirname(os.path.abspath(__file__))
shutil.copy(os.path.join(aqui, "..", "backend", "app", "push.py"), os.path.join(raiz, "app", "push.py"))
m = os.path.join(raiz, "app", "main.py")
s = open(m, encoding="utf-8").read()
if "push_router" not in s:
    shutil.copy(m, m + ".bak6")
    s = s.replace("from app.auth.signup import router as signup_router  # LINK_SOCIAL",
                  "from app.auth.signup import router as signup_router  # LINK_SOCIAL\nfrom app.push import router as push_router", 1)
    s = s.replace('app.include_router(signup_router, prefix="/auth", tags=["auth"])',
                  'app.include_router(signup_router, prefix="/auth", tags=["auth"])\napp.include_router(push_router, prefix="/push", tags=["push"])', 1)
    assert "push_router, prefix" in s
    open(m, "w", encoding="utf-8").write(s)
print("aplicado")
