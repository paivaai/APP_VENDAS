"""Agentes de IA. Fluxo: evento -> agente decide (2 opções + consequências)
-> grava em suggestions -> WhatsApp (Evolution API) -> cliente aprova ->
executa -> atualiza painel.

Modelos vêm do ambiente (CLAUDE_MODEL_FAST / CLAUDE_MODEL_COMPLEX):
rápido/barato para rotina, o maior só para decisão complexa.
"""
import os
import anthropic

REQUIRED_FIELDS = {
    "mercado_livre": ["title", "description", "price", "sku", "stock", "category_hint"],
    "shopee": ["title", "description", "price", "sku", "stock"],
    "shein": ["title", "description", "price", "sku", "stock", "images"],
    "tiktok": ["title", "description", "price", "sku", "stock", "images"],
}


class ClaudeAgent:
    name = "base"

    def _client(self):
        # chave lida em tempo de chamada, não no import
        return anthropic.Anthropic()

    def _model(self, complex_task: bool) -> str:
        return os.getenv("CLAUDE_MODEL_COMPLEX" if complex_task else "CLAUDE_MODEL_FAST", "")

    def analyze(self, context: str, tenant_id: str, complex_task: bool = False, db=None) -> str:
        model = self._model(complex_task)
        resp = self._client().messages.create(
            model=model,
            max_tokens=1000,
            messages=[{"role": "user", "content": context}],
        )
        if db is not None:
            from app.models import ApiUsage
            db.add(ApiUsage(
                tenant_id=tenant_id, agent=self.name, model=model,
                input_tokens=resp.usage.input_tokens, output_tokens=resp.usage.output_tokens,
            ))
            db.commit()
        return resp.content[0].text


class PreSaleAgent(ClaudeAgent):
    """Cadastro de produto (planilha + imagens)."""
    name = "pre_sale"

    def validate_product_row(self, row: dict, marketplace: str) -> list[str]:
        """Campos obrigatórios ausentes ou vazios para o marketplace."""
        required = REQUIRED_FIELDS.get(marketplace, [])
        return [f for f in required if not row.get(f)]

    def normalize_product_row(self, row: dict) -> dict:
        out = dict(row)
        for k in ("title", "description", "sku"):
            if isinstance(out.get(k), str):
                out[k] = out[k].strip()
        if out.get("price") is not None:
            try:
                out["price"] = round(float(str(out["price"]).replace(",", ".")), 2)
            except ValueError:
                pass
        return out

    def process_product_row(self, row: dict, marketplace: str, tenant_id: str, db) -> dict:
        """Decide: tudo certo -> ready_to_register; falta algo -> pending + WhatsApp."""
        from app.models import ProductSuggestion
        normalized = self.normalize_product_row(row)
        missing = self.validate_product_row(normalized, marketplace)
        s = ProductSuggestion(
            tenant_id=tenant_id, marketplace=marketplace, raw_data=row,
            normalized_data=normalized, missing_fields=missing or None,
            status="pending" if missing else "ready_to_register",
            decided_via=None if missing else "auto",
        )
        db.add(s)
        db.commit()
        if missing:
            self.request_missing_info_via_whatsapp(s)
        return {"id": s.id, "status": s.status, "missing_fields": missing}

    def request_missing_info_via_whatsapp(self, suggestion) -> None:
        # TODO: integrar Evolution API (instância PRE_SALE do tenant)
        pass

    # TODO: mapeamento de categoria por marketplace (modelo complexo) e chamada real
    # às APIs quando status == "ready_to_register".


class SaleAgent(ClaudeAgent):
    """Cupom/desconto, alertas e aprovações. TODO: implementar."""
    name = "sale"


class PostSaleAgent(ClaudeAgent):
    """Devoluções, cancelamentos e respostas. TODO: implementar."""
    name = "post_sale"
