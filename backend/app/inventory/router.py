from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Product, TikTokAccount
from app.auth.router import get_current_user

router = APIRouter()

@router.get("/")
def list_products(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    accounts = db.query(TikTokAccount).filter(TikTokAccount.user_id == current_user.id).all()
    account_ids = [a.id for a in accounts]
    products = db.query(Product).filter(Product.tiktok_account_id.in_(account_ids)).all()
    return [{"id": p.id, "name": p.name, "price": p.price, "stock": p.stock, "status": p.status} for p in products]
