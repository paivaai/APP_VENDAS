import logging
logger = logging.getLogger(__name__)
"""Mercado Livre OAuth Authentication"""
import os
import httpx
from typing import Optional, Dict
from urllib.parse import urlencode
from datetime import datetime, timedelta

class MercadoLivreOAuth:
    """Handles OAuth flow for Mercado Livre integration.
    Supports obtaining access tokens and refreshing them.
    """

    BASE_URL = "https://auth.mercadolivre.com.br"
    API_BASE_URL = "https://api.mercadolibre.com"

    def __init__(self):
        self.app_id = os.getenv("ML_APP_ID")
        self.client_secret = os.getenv("ML_CLIENT_SECRET")
        self.redirect_uri = os.getenv("ML_REDIRECT_URI")

        if not all([self.app_id, self.client_secret, self.redirect_uri]):
            raise ValueError("Missing Mercado Livre OAuth configuration")

    def get_auth_url(self, tenant_id: str, state: Optional[str] = None) -> str:
        """Generate the authorization URL for Mercado Livre OAuth flow.

        Args:
            tenant_id: The tenant ID for tracking
            state: State parameter for CSRF protection

        Returns:
            Authorization URL
        """
        params = {
            "response_type": "code",
            "client_id": self.app_id,
            "redirect_uri": self.redirect_uri,
            "state": state or tenant_id,
        }

        auth_url = f"{self.BASE_URL}/authorization?{urlencode(params)}"
        return auth_url

    async def exchange_code(self, code: str) -> Dict[str, any]:
        """
        Exchange authorization code for access token.

        Args:
            code: Authorization code from callback

        Returns:
            Token response containing access_token, refresh_token, etc.
        """
        async with httpx.AsyncClient() as client:
            logger.info(f"exchange_code: client_id={self.app_id}")
            logger.info(f"exchange_code: redirect_uri={self.redirect_uri}")
            logger.info(f"exchange_code: code={code[:15]}...")
            response = await client.post(
                f"{self.API_BASE_URL}/oauth/token",
                data={
                    "grant_type": "authorization_code",
                    "client_id": self.app_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": self.redirect_uri,
                },
                timeout=30.0,
            )
            logger.info(f"exchange_code response status: {response.status_code}")
            if response.status_code != 200:
                logger.error(f"exchange_code error response: {response.text}")
            response.raise_for_status()
            return response.json()

    async def refresh_token(self, refresh_token: str) -> Dict[str, any]:
        """
        Refresh an expired access token.

        Args:
            refresh_token: The refresh token

        Returns:
            New token response
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.API_BASE_URL}/oauth/token",
                data={
                    "grant_type": "refresh_token",
                    "client_id": self.app_id,
                    "client_secret": self.client_secret,
                    "refresh_token": refresh_token,
                },
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    async def get_user_info(self, access_token: str) -> Dict[str, any]:
        """
        Get authenticated user information from Mercado Libre.

        Args:
            access_token: Valid access token

        Returns:
            User information
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.API_BASE_URL}/users/me",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()
