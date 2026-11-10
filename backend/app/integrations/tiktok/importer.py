import os
import json
import subprocess
import httpx

from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models import TikTokAccount, Product, Order

APP_KEY = os.getenv("TIKTOK_APP_KEY")
APP_SECRET = os.getenv("TIKTOK_APP_SECRET")
SIGNER_PATH = "/opt/tiktok-signer/signer.php"


async def refresh_token_if_needed(account: TikTokAccount, db: Session) -> bool:
    if (
        account.token_expires_at
        and account.token_expires_at > datetime.utcnow() + timedelta(hours=1)
        and account.access_token
    ):
        return True

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            "https://auth.tiktok-shops.com/api/v2/token/refresh",
            params={
                "app_key": APP_KEY,
                "app_secret": APP_SECRET,
                "refresh_token": account.refresh_token,
                "grant_type": "refresh_token",
            },
        )

    data = resp.json()
    print("REFRESH RAW:", data)

    if data.get("code") != 0:
        print(f"Refresh error: {data}")
        return False

    result = data.get("data") or {}
    account.access_token = result.get("access_token")
    account.refresh_token = result.get("refresh_token", account.refresh_token)

    expires_in = result.get("access_token_expire_in", 0) or 0
    account.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

    db.add(account)
    db.commit()
    db.refresh(account)
    return True


def run_signer(access_token: str, shop_cipher: str, action: str) -> dict:
    cmd = [
        "php",
        SIGNER_PATH,
        access_token,
        shop_cipher or "",
        action,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    stdout = (result.stdout or "").strip()
    stderr = (result.stderr or "").strip()

    if result.returncode != 0:
        print("SIGNER STDERR:", stderr)
        return {"error": stderr or "Signer falhou"}

    try:
        data = json.loads(stdout)
        print(f"{action.upper()} RAW:", data)
        return data
    except Exception:
        print(f"{action.upper()} RAW TEXT:", stdout)
        return {"error": "Resposta inválida do signer", "raw": stdout}


async def import_products(account: TikTokAccount, db: Session) -> int:
    data = run_signer(account.access_token, account.shop_cipher, "products")

    if data.get("error"):
        print("Products signer error:", data)
        return 0

    products = data.get("products", []) or []
    count = 0

    for p in products:
        tiktok_product_id = str(p.get("id"))
        if not tiktok_product_id or tiktok_product_id == "None":
            continue

        obj = db.query(Product).filter(
            Product.tiktok_account_id == account.id,
            Product.tiktok_product_id == tiktok_product_id,
        ).first()

        if not obj:
            obj = Product(
                tiktok_account_id=account.id,
                tiktok_product_id=tiktok_product_id,
            )

        obj.name = p.get("title") or p.get("name") or ""
        obj.status = p.get("status", "")

        skus = p.get("skus", []) or []

        prices = []
        stock_total = 0

        for sku in skus:
            price_info = sku.get("price", {}) or {}
            try:
                if price_info.get("tax_exclusive_price") is not None:
                    prices.append(float(price_info.get("tax_exclusive_price") or 0))
                elif price_info.get("original_price") is not None:
                    prices.append(float(price_info.get("original_price") or 0))
            except Exception:
                pass

            inventory = sku.get("inventory", []) or []
            for inv in inventory:
                try:
                    stock_total += int(inv.get("quantity", 0) or 0)
                except Exception:
                    pass

        obj.price = prices[0] if prices else 0
        obj.stock = stock_total
        obj.updated_at = datetime.utcnow()

        db.add(obj)
        count += 1

    db.commit()
    return count


async def import_orders(account: TikTokAccount, db: Session) -> int:
    data = run_signer(account.access_token, account.shop_cipher, "orders")

    if data.get("error"):
        print("Orders signer error:", data)
        return 0

    orders = data.get("orders", []) or []
    count = 0

    for o in orders:
        tiktok_order_id = str(o.get("id"))
        if not tiktok_order_id or tiktok_order_id == "None":
            continue

        obj = db.query(Order).filter(
            Order.tiktok_account_id == account.id,
            Order.tiktok_order_id == tiktok_order_id,
        ).first()

        if not obj:
            obj = Order(
                tiktok_account_id=account.id,
                tiktok_order_id=tiktok_order_id,
            )

        obj.status = o.get("status", "")

        payment = o.get("payment", {}) or {}
        try:
            total = float(payment.get("total_amount", 0) or 0)
        except Exception:
            total = 0

        if hasattr(obj, "total"):
            obj.total = total
        if hasattr(obj, "total_amount"):
            obj.total_amount = total

        create_time = o.get("create_time")
        if create_time:
            try:
                obj.created_at = datetime.utcfromtimestamp(int(create_time))
            except Exception:
                obj.created_at = datetime.utcnow()
        else:
            obj.created_at = datetime.utcnow()

        db.add(obj)
        count += 1

    db.commit()
    return count


async def run_full_import(account_id: str, db: Session):
    account = db.query(TikTokAccount).filter(TikTokAccount.id == account_id).first()
    if not account:
        return {"error": "Conta não encontrada"}

    if not account.shop_cipher:
        return {"error": "shop_cipher não encontrado"}

    ok = await refresh_token_if_needed(account, db)
    if not ok:
        return {"error": "Falha ao renovar token"}

    products = await import_products(account, db)
    orders = await import_orders(account, db)

    return {
        "products": products,
        "orders": orders,
    }
