from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Recommendation, Product, TikTokAccount
from app.auth.router import get_current_user
import anthropic, os

router = APIRouter()

LOW_STOCK_THRESHOLD = 10
MIN_MARGIN_FOR_DISCOUNT = 0.30

@router.get("/")
def list_recommendations(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    accounts = db.query(TikTokAccount).filter(TikTokAccount.user_id == current_user.id).all()
    account_ids = [a.id for a in accounts]
    recs = db.query(Recommendation).filter(
        Recommendation.tiktok_account_id.in_(account_ids)
    ).order_by(Recommendation.created_at.desc()).limit(50).all()
    return [{
        "id": r.id,
        "type": r.type,
        "rule": r.rule_triggered,
        "suggested_value": r.suggested_value,
        "justification": r.ai_justification,
        "is_read": r.is_read,
        "created_at": str(r.created_at)
    } for r in recs]

@router.post("/analyze")
def analyze(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    accounts = db.query(TikTokAccount).filter(TikTokAccount.user_id == current_user.id).all()
    if not accounts:
        return {"message": "Nenhuma conta TikTok conectada"}

    account_ids = [a.id for a in accounts]
    products = db.query(Product).filter(Product.tiktok_account_id.in_(account_ids)).all()
    generated = []

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    for product in products:
        rule = None
        rec_type = None
        suggested_value = None

        if product.stock is not None and product.stock < LOW_STOCK_THRESHOLD:
            rule = f"Estoque baixo: {product.stock} unidades restantes"
            rec_type = "low_stock"
            suggested_value = float(product.stock)

        elif product.price and product.cost:
            margin = (product.price - product.cost) / product.price
            if margin >= MIN_MARGIN_FOR_DISCOUNT:
                rule = f"Margem de {margin*100:.0f}% permite desconto"
                rec_type = "discount"
                suggested_value = round(margin * 0.5 * 100, 0)

        if not rule:
            continue

        prompt = f"""Você é um especialista em e-commerce TikTok Shop no Brasil.
Produto: {product.name}
Preço: R$ {product.price}
Estoque: {product.stock} unidades
Regra disparada: {rule}

Em 2 frases curtas e diretas em português, explique por que essa recomendação faz sentido para o vendedor agir agora."""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        justification = message.content[0].text

        rec = Recommendation(
            tiktok_account_id=accounts[0].id,
            product_id=product.id,
            type=rec_type,
            rule_triggered=rule,
            suggested_value=suggested_value,
            ai_justification=justification
        )
        db.add(rec)
        generated.append({"product": product.name, "type": rec_type})

    db.commit()
    return {"generated": len(generated), "recommendations": generated}
