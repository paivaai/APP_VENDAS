import os
import httpx
from datetime import datetime, timedelta
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

SHOPEE_PARTNER_ID = os.getenv("SHOPEE_PARTNER_ID", "740097670")
SHOPEE_PARTNER_KEY = os.getenv("SHOPEE_PARTNER_KEY", "")
SHOPEE_AUTH_URL = "https://partner.shopeemenus.com/api/v2/oauth/authorize"
SHOPEE_TOKEN_URL = "https://partner.shopeemenus.com/api/v2/oauth/token"
SHOPEE_REDIRECT_URI = os.getenv("SHOPEE_REDIRECT_URI", "https://api.pdp.paivaai.com.br/integrations/shopee/callback")

class ShopeeIntegration:
    """Cliente para integração com API do Shopee"""

    def __init__(self, access_token: str = None, refresh_token: str = None):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.client = httpx.AsyncClient()

    def get_auth_url(self, tenant_id: str) -> str:
        """Retorna URL de autenticação OAuth"""
        return (
            f"{SHOPEE_AUTH_URL}?"
            f"client_id={SHOPEE_PARTNER_ID}&"
            f"redirect_uri={SHOPEE_REDIRECT_URI}&"
            f"response_type=code&"
            f"state={tenant_id}"
        )

    async def exchange_code(self, code: str) -> Dict[str, Any]:
        """Troca authorization code por access token"""
        payload = {
            "client_id": SHOPEE_PARTNER_ID,
            "client_secret": SHOPEE_PARTNER_KEY,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": SHOPEE_REDIRECT_URI
        }

        async with self.client as client:
            response = await client.post(SHOPEE_TOKEN_URL, json=payload)
            data = response.json()

        return {
            "access_token": data.get("access_token"),
            "refresh_token": data.get("refresh_token"),
            "expires_in": data.get("expires_in"),
            "expires_at": (datetime.utcnow() + timedelta(seconds=data.get("expires_in", 21600))).isoformat()
        }

    async def get_shop_info(self) -> Dict[str, Any]:
        """Obtém informações da loja"""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        url = "https://partner.shopeemenus.com/api/v2/shops"

        async with self.client as client:
            response = await client.get(url, headers=headers)
            return response.json()

    async def get_orders(self, shop_id: str, limit: int = 50) -> Dict[str, Any]:
        """Lista pedidos da loja"""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        url = f"https://partner.shopeemenus.com/api/v2/shops/{shop_id}/orders?limit={limit}"

        async with self.client as client:
            response = await client.get(url, headers=headers)
            return response.json()

    async def get_products(self, shop_id: str, status: str = "NORMAL") -> Dict[str, Any]:
        """Lista produtos da loja"""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        url = f"https://partner.shopeemenus.com/api/v2/shops/{shop_id}/products?status={status}"

        async with self.client as client:
            response = await client.get(url, headers=headers)
            return response.json()

    async def close(self):
        """Fecha a conexão HTTP"""
        await self.client.aclose()
