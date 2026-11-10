from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.database import Base, engine, get_db
from app.auth.utils import get_current_user
from app.agents.orchestrator import PreSaleAgent
from app.integrations.bling.router import router as bling_router

app = FastAPI(title="PDP — Paiva AI Decision Platform")

if engine is not None:
    Base.metadata.create_all(engine)  # TODO: trocar por Alembic


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(bling_router, prefix="/integrations/bling", tags=["bling"])
# TODO: auth (register/login), mercadolivre, tiktok, shopee — recuperar da VPS.


@app.post("/agents/pre-sale/register", tags=["agents"])
def pre_sale_register(payload: dict, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """payload: {"marketplace": "shopee", "row": {...}}"""
    return PreSaleAgent().process_product_row(
        payload["row"], payload["marketplace"], user.tenant_id, db
    )
