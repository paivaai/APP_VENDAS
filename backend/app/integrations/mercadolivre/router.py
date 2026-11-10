"""Mercado Livre Integration Routes"""
from fastapi import Depends, APIRouter, Query, HTTPException, Request
from fastapi.responses import RedirectResponse
from typing import Optional
from app.integrations.mercadolivre.oauth import MercadoLivreOAuth
from app.integrations.mercadolivre.claude_service import ClaudeService

from app.auth.router import get_current_user as _exigir_login
router = APIRouter()
oauth = MercadoLivreOAuth()
claude = ClaudeService()


@router.get("/auth/connect")
async def connect_mercadolivre(tenant_id: str = Query(...)):
    """
    Initiate Mercado Livre OAuth flow.
    Redirects user to Mercado Livre login.
    
    Args:
        tenant_id: The tenant identifier
    """
    try:
        auth_url = oauth.get_auth_url(tenant_id)
        return RedirectResponse(url=auth_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/auth/callback")
async def mercadolivre_callback(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
):
    """
    Handle Mercado Livre OAuth callback.
    Exchanges code for access token.
    
    Args:
        code: Authorization code from Mercado Livre
        state: State parameter (should contain tenant_id)
        error: Error parameter if authorization failed
    """
    if error:
        return {
            "success": False,
            "error": error,
            "message": "Authorization failed",
        }
    
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")
    
    try:
        token_response = await oauth.exchange_code(code)
        
        # Get user info
        user_info = await oauth.get_user_info(token_response["access_token"])
        if state == "login":  # LOGIN_SOCIAL_ML
            from app.integrations.mercadolivre.login import finish_login
            return finish_login(token_response, user_info)
        if state and state.startswith("link:"):
            from app.integrations.mercadolivre.login import finish_link
            return finish_link(state, token_response, user_info)
        
        return {
            "success": True,
            "tenant_id": state,
            "user_id": user_info.get("id"),
            "nickname": user_info.get("nickname"),
            "email": user_info.get("email"),
            
            
            "expires_in": token_response.get("expires_in"),
            "message": "Successfully connected to Mercado Livre",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token exchange failed: {str(e)}")


@router.post("/analyze", dependencies=[Depends(_exigir_login)])
async def analyze_product(
    product_data: dict,
    tenant_id: str = Query(...),
    complex: bool = Query(False),
):
    """
    Analyze a Mercado Livre product using Claude AI.
    
    Args:
        product_data: Product information
        tenant_id: Tenant identifier
        complex: Use Sonnet (complex) vs Haiku (simple) model
    """
    try:
        result = await claude.analyze_product(
            product_data=product_data,
            tenant_id=tenant_id,
            complex=complex,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ask", dependencies=[Depends(_exigir_login)])
async def ask_claude(
    question: str = Query(...),
    context: Optional[dict] = None,
    tenant_id: Optional[str] = Query(None),
    complex: bool = Query(False),
):
    """
    Ask Claude a question about marketplace data.
    
    Args:
        question: The question to ask
        context: Optional context data
        tenant_id: Optional tenant identifier
        complex: Use complex model
    """
    try:
        result = await claude.ask(
            question=question,
            context=context,
            tenant_id=tenant_id,
            complex=complex,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


from app.integrations.mercadolivre.login import router as _login_router  # LOGIN_SOCIAL_ML
router.include_router(_login_router)
