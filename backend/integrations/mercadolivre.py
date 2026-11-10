import os
import aiohttp
import httpx
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import json

ML_APP_ID = os.getenv("ML_APP_ID", "2642305269630590")
ML_CLIENT_SECRET = os.getenv("ML_CLIENT_SECRET")
ML_REDIRECT_URI = os.getenv("ML_REDIRECT_URI", "https://api.pdp.paivaai.com.br/integrations/mercadolivre/callback")
ML_AUTH_URL = "https://auth.mercadolivre.com.br/authorization"
ML_TOKEN_URL = "https://api.mercadolivre.com/oauth/token"
ML_API_BASE = "https://api.mercadolivre.com"


class MercadoLivreIntegration:
    """Integração com API do Mercado Livre"""
    
    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token
        self.client = httpx.AsyncClient()
    
    def get_auth_url(self, tenant_id: str) -> str:
        """Retorna URL de autenticação OAuth"""
        return (
            f"{ML_AUTH_URL}?response_type=code&"
            f"client_id={ML_APP_ID}&"
            f"redirect_uri={ML_REDIRECT_URI}&"
            f"state={tenant_id}"
        )
    
    async def exchange_code(self, code: str) -> Dict[str, Any]:
        """Troca authorization code por tokens"""
        payload = {
            "grant_type": "authorization_code",
            "client_id": ML_APP_ID,
            "client_secret": ML_CLIENT_SECRET,
            "code": code,
            "redirect_uri": ML_REDIRECT_URI
        }
        
        async with self.client as client:
            response = await client.post(ML_TOKEN_URL, json=payload)
            data = response.json()
            
            return {
                "access_token": data.get("access_token"),
                "refresh_token": data.get("refresh_token"),
                "expires_in": data.get("expires_in"),
                "expires_at": (datetime.utcnow() + timedelta(seconds=data.get("expires_in", 21600))).isoformat()
            }
    
    async def refresh_token_ml(self, refresh_token: str) -> Dict[str, Any]:
        """Renova access token usando refresh token"""
        payload = {
            "grant_type": "refresh_token",
            "client_id": ML_APP_ID,
            "client_secret": ML_CLIENT_SECRET,
            "refresh_token": refresh_token
        }
        
        async with self.client as client:
            response = await client.post(ML_TOKEN_URL, json=payload)
            data = response.json()
            
            return {
                "access_token": data.get("access_token"),
                "refresh_token": data.get("refresh_token"),
                "expires_in": data.get("expires_in"),
                "expires_at": (datetime.utcnow() + timedelta(seconds=data.get("expires_in", 21600))).isoformat()
            }
    
    async def get_orders(self, seller_id: str, limit: int = 50) -> Dict[str, Any]:
        """Lista pedidos do vendedor"""
        url = f"{ML_API_BASE}/orders/search?seller_id={seller_id}&limit={limit}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        async with self.client as client:
            response = await client.get(url, headers=headers)
            return response.json()
    
    async def get_products(self, seller_id: str, status: str = "active") -> Dict[str, Any]:
        """Lista produtos do vendedor"""
        url = f"{ML_API_BASE}/users/{seller_id}/listings?status={status}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        async with self.client as client:
            response = await client.get(url, headers=headers)
            return response.json()
    
    async def get_metrics(self, seller_id: str) -> Dict[str, Any]:
        """Retorna métricas gerais (receita, conversão, visitas)"""
        url = f"{ML_API_BASE}/users/{seller_id}/details"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        async with self.client as client:
            response = await client.get(url, headers=headers)
            data = response.json()
            
            return {
                "seller_id": seller_id,
                "user_id": data.get("id"),
                "nickname": data.get("nickname"),
                "status": data.get("status"),
                "seller_reputation": data.get("seller_reputation"),
                "points": data.get("points")
            }
    
    async def create_coupon(self, campaign_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Cria cupom de desconto"""
        url = f"{ML_API_BASE}/campaigns/{campaign_id}/coupons"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        async with self.client as client:
            response = await client.post(url, json=payload, headers=headers)
            return response.json()
    
    async def update_price(self, item_id: str, price: float) -> Dict[str, Any]:
        """Atualiza preço de um produto"""
        url = f"{ML_API_BASE}/items/{item_id}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        payload = {"price": price}
        
        async with self.client as client:
            response = await client.put(url, json=payload, headers=headers)
            return response.json()
    
    async def close(self):
        """Fecha a conexão HTTP"""
        await self.client.aclose()
