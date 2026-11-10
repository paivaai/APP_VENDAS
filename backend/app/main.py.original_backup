from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.auth.router import router as auth_router
from app.integrations.tiktok.router import router as tiktok_router
from app.orders.router import router as orders_router
# from app.integrations.mercadolivre.router import router as mercadolivre_router
from app.inventory.router import router as inventory_router
from app.decisions.router import router as decisions_router

app = FastAPI(title="Paiva AI Decision Platform", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(tiktok_router, prefix="/integrations/tiktok", tags=["tiktok"])
app.include_router(orders_router, prefix="/orders", tags=["orders"])
app.include_router(inventory_router, prefix="/inventory", tags=["inventory"])
app.include_router(decisions_router, prefix="/decisions", tags=["decisions"])
# app.include_router(mercadolivre_router, prefix="/integrations/mercadolivre", tags=["mercadolivre"])

@app.get("/")
def root():
    return {"status": "ok", "app": "Paiva AI Decision Platform"}

@app.get("/health")
def health():
    return {"status": "healthy"}
