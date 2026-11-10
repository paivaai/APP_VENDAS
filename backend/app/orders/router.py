from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Order, TikTokAccount
from app.auth.router import get_current_user

router = APIRouter()

@router.get("/")
def list_orders(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    accounts = db.query(TikTokAccount).filter(TikTokAccount.user_id == current_user.id).all()
    account_ids = [a.id for a in accounts]
    orders = db.query(Order).filter(Order.tiktok_account_id.in_(account_ids)).order_by(Order.created_at.desc()).limit(100).all()
    return [{"id": o.id, "tiktok_order_id": o.tiktok_order_id, "status": o.status, "total": o.total_amount, "created_at": str(o.created_at)} for o in orders]
