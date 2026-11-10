"""Agente de perguntas dos compradores (Mercado Livre): lê perguntas sem resposta e sugere resposta com Claude.

Uso na VPS:  python3 patch_perguntas.py /opt/pdp/backend/app/integrations/mercadolivre
Idempotente. Somente leitura no Mercado Livre. Sem ANTHROPIC_API_KEY no .env devolve as perguntas sem sugestão.
Não devolve dado pessoal do comprador (nem o id dele).
"""
import sys, os, shutil

pasta = sys.argv[1]
lg = os.path.join(pasta, "login.py")
t = open(lg, encoding="utf-8").read()
if "PERGUNTAS_ML" in t:
    print("já aplicado"); sys.exit(0)
shutil.copy(lg, lg + ".bak5")
t += '''

# PERGUNTAS_ML: perguntas sem resposta + rascunho de resposta (somente leitura)
async def _rascunho(c, pergunta, item, descricao):
    chave = os.getenv("ANTHROPIC_API_KEY")
    if not chave:
        return None
    attrs = "; ".join(
        "%s: %s" % (a.get("name"), a.get("value_name")) for a in (item.get("attributes") or [])[:12] if a.get("value_name"))
    prompt = (
        "Você responde perguntas de compradores no Mercado Livre em nome do vendedor.\\n"
        "Use SOMENTE as informações do anúncio abaixo. Se a informação não estiver nele, diga que vai confirmar e retornar. "
        "Nunca invente medidas, prazos, garantia ou compatibilidade. Português do Brasil, cordial, direto, no máximo 3 frases, "
        "sem pedir contato fora do Mercado Livre.\\n\\n"
        "Título: %s\\nPreço: R$ %s\\nEstoque: %s\\nCondição: %s\\nGarantia: %s\\nAtributos: %s\\nDescrição: %s\\n\\n"
        "Pergunta do comprador: %s\\n\\nEscreva apenas a resposta."
        % (item.get("title"), item.get("price"), item.get("available_quantity"), item.get("condition"),
           item.get("warranty"), attrs, (descricao or "")[:900], pergunta))
    try:
        r = await c.post("https://api.anthropic.com/v1/messages",
                         headers={"x-api-key": chave, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                         json={"model": os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5"), "max_tokens": 300,
                               "messages": [{"role": "user", "content": prompt}]}, timeout=40.0)
        if r.status_code != 200:
            return None
        return r.json()["content"][0]["text"].strip()
    except Exception:
        return None


@router.get("/perguntas")
async def perguntas_ml(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    acc = db.query(MLAccount).filter(MLAccount.user_id == current_user.id).first()
    if not acc:
        return []
    tok = await _token_valido(db, acc)
    h = {"Authorization": "Bearer " + tok}
    saida = []
    async with httpx.AsyncClient() as c:
        r = await c.get(API + "/questions/search", headers=h, timeout=30.0, params={
            "seller_id": acc.ml_user_id, "status": "UNANSWERED", "sort_fields": "date_created", "sort_types": "DESC", "limit": 5})
        if r.status_code != 200:
            raise HTTPException(status_code=502, detail="Mercado Livre não respondeu as perguntas")
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
                "id": str(q.get("id")), "text": q.get("text"), "date_created": q.get("date_created"),
                "item_title": item.get("title"), "price": item.get("price"), "stock": item.get("available_quantity"),
                "draft": await _rascunho(c, q.get("text"), item, desc)})
    return saida
'''
open(lg, "w", encoding="utf-8").write(t)
print("aplicado")
