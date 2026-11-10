import os
import httpx
from datetime import datetime, timedelta
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

SHEIN_CLIENT_ID = os.getenv("SHEIN_CLIENT_ID", "2585798034")
SHEIN_CLIENT_SECRET = os.getenv("SHEIN_CLIENT_SECRET", "")
SHEIN_AUTH_URL = "https://api.zerofinance.com/seller/oauth/authorize"
SHEIN_TOKEN_URL = "https://api.zerofinance.com/seller/oauth/token"
SHEIN_API_BASE = "https://api.zerofinance.com/seller"
SHEIN_REDIRECT_URI = os.getenv("SHEIN_REDIRECT_URI", "https://api.pdp.paivaai.com.br/integrations/shein/callback")

class SheinIntegration:
    """Cliente para integração com API do Shein"""

    def __init__(self, access_token: str = None, refresh_token: str = None):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.client = httpx.AsyncClient()

    def get_auth_url(self, tenant_id: str) -> str:
        """Retorna URL de autenticação OAuth"""
        return (
            f"{SHEIN_AUTH_URL}?"
            f"client_id={SHEIN_CLIENT_ID}&"
            f"redirect_uri={SHEIN_REDIRECT_URI}&"
            f"response_type=code&"
            f"state={tenant_id}&"
            f"scope=order.view,product.view"
        )

    async def exchange_code(self, code: str) -> Dict[str, Any]:
        """Troca authorization code por access token"""
        payload = {
            "client_id": SHEIN_CLIENT_ID,
            "client_secret": SHEIN_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": SHEIN_REDIRECT_URI
        }

        async with self.client as client:
            response = await client.post(SHEIN_TOKEN_URL, json=payload)
            data = response.json()

        return {
            "access_token": data.get("access_token"),
            "refresh_token": data.get("refresh_token"),
            "expires_in": data.get("expires_in"),
            "expires_at": (datetime.utcnow() + timedelta(seconds=data.get("expires_in", 3600))).isoformat()
        }

    async def get_seller_info(self) -> Dict[str, Any]:
        """Obtém informações do vendedor"""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        url = f"{SHEIN_API_BASE}/seller"

        async with self.client as client:
            response = await client.get(url, headers=headers)
            return response.json()

    async def get_orders(self, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """Lista pedidos do vendedor"""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        url = f"{SHEIN_API_BASE}/orders?limit={limit}&offset={offset}"

        async with self.client as client:
            response = await client.get(url, headers=headers)
            return response.json()

    async def get_products(self, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """Lista produtos do vendedor"""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        url = f"{SHEIN_API_BASE}/products?limit={limit}&offset={offset}"

        async with self.client as client:
            response = await client.get(url, headers=headers)
            return response.json()

    async def get_order_detail(self, order_id: str) -> Dict[str, Any]:
        """Obtém detalhes de um pedido"""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        url = f"{SHEIN_API_BASE}/orders/{order_id}"

        async with self.client as client:
            response = await client.get(url, headers=headers)
            return response.json()

    async def close(self):
        """Fecha a conexão HTTP"""
        await self.client.aclose()
