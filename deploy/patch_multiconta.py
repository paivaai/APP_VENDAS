"""Várias lojas do Mercado Livre por usuário (/orders, /me, /perguntas passam a ler todas as contas).

Uso na VPS:  python3 patch_multiconta.py /opt/pdp/backend/app/integrations/mercadolivre
Idempotente. Backup login.py.bak7. Só leitura no Mercado Livre.
"""
import sys, os, shutil
lg = os.path.join(sys.argv[1], "login.py")
t = open(lg, encoding="utf-8").read()
if "MULTICONTA_ML" in t:
    print("já aplicado"); sys.exit(0)
shutil.copy(lg, lg + ".bak7")

# 1) /orders e /me
i = t.index('@router.get("/orders")')
j = t.index("# LINK_SOCIAL")
novo = '''@router.get("/orders")
async def pedidos_ml(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """MULTICONTA_ML: pedidos de todas as lojas do vendedor. Só id, status, valor e data: nunca dados do comprador."""
    accs = db.query(MLAccount).filter(MLAccount.user_id == current_user.id).all()
    saida = []
    for acc in accs:
        try:
            tok = await _token_valido(db, acc)
            async with httpx.AsyncClient() as c:
                r = await c.get(API + "/orders/search", params={"seller": acc.ml_user_id, "sort": "date_desc", "limit": 50},
                                headers={"Authorization": "Bearer " + tok}, timeout=30.0)
        except Exception:
            continue
        if r.status_code != 200:
            continue
        saida += [{"id": str(o.get("id")), "order_id": str(o.get("id")), "status": o.get("status"),
                   "total": o.get("total_amount"), "created_at": o.get("date_created"), "channel": "Mercado Livre",
                   "store": acc.nickname} for o in r.json().get("results", [])]
    return saida


@router.get("/me")
def quem_sou_eu(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    accs = db.query(MLAccount).filter(MLAccount.user_id == current_user.id).all()
    return {"connected": bool(accs), "nickname": accs[0].nickname if accs else None, "stores": [a.nickname for a in accs]}


'''
t = t[:i] + novo + t[j:]

# 2) /perguntas
if '@router.get("/perguntas")' in t:
    k = t.index('@router.get("/perguntas")')
    t = t[:k] + '''@router.get("/perguntas")
async def perguntas_ml(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    accs = db.query(MLAccount).filter(MLAccount.user_id == current_user.id).all()
    saida = []
    for acc in accs:
        if len(saida) >= 6:
            break
        try:
            tok = await _token_valido(db, acc)
        except Exception:
            continue
        h = {"Authorization": "Bearer " + tok}
        async with httpx.AsyncClient() as c:
            r = await c.get(API + "/questions/search", headers=h, timeout=30.0, params={
                "seller_id": acc.ml_user_id, "status": "UNANSWERED", "sort_fields": "date_created", "sort_types": "DESC", "limit": 5})
            if r.status_code != 200:
                continue
            for q in r.json().get("questions", []):
                item, desc = {}, ""
                try:
                    ir = await c.get(API + "/items/" + str(q.get("item_id")), headers=h, timeout=30.0)
                    if ir.status_code == 200:
                        item = ir.json()
                    dr = await c.get(API + "/items/" + str(q.get("item_id")) + "/description", headers=h, timeout=30.0)
                    if dr.status_code == 200:
                        desc = dr.json().get("plain_text") or ""
                except Exception:
                    pass
                saida.append({
                    "id": str(q.get("id")), "text": q.get("text"), "date_created": q.get("date_created"), "store": acc.nickname,
                    "item_title": item.get("title"), "price": item.get("price"), "stock": item.get("available_quantity"),
                    "draft": await _rascunho(c, q.get("text"), item, desc)})
    return saida
'''
open(lg, "w", encoding="utf-8").write(t)
print("aplicado")
