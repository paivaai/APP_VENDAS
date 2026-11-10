# Endpoints para Shopee e Shein
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from database import get_db
from models import ShopeeIntegration, SheinIntegration
from integrations.shopee import ShopeeIntegration as ShopeeClient
from integrations.shein import SheinIntegration as SheinClient
import os
from datetime import datetime

router = APIRouter()

# ===== SHOPEE =====

@router.get("/integrations/shopee/connect")
async def shopee_connect(tenant_id: UUID):
    """Retorna URL OAuth do Shopee"""
    client = ShopeeClient()
    return {"auth_url": client.get_auth_url(str(tenant_id))}


@router.get("/integrations/shopee/callback")
async def shopee_callback(code: str, state: str, db: Session = Depends(get_db)):
    """Troca code por access token e salva"""
    try:
        client = ShopeeClient()
        token_data = await client.exchange_code(code)
        
        # Verificar se já existe integração para este tenant
        existing = db.query(ShopeeIntegration).filter(
            ShopeeIntegration.tenant_id == UUID(state)
        ).first()
        
        if existing:
            # Atualizar
            existing.access_token = token_data["access_token"]
            existing.refresh_token = token_data["refresh_token"]
            existing.expires_at = datetime.fromisoformat(token_data["expires_at"])
        else:
            # Criar nova
            new_integration = ShopeeIntegration(
                tenant_id=UUID(state),
                access_token=token_data["access_token"],
                refresh_token=token_data["refresh_token"],
                expires_at=datetime.fromisoformat(token_data["expires_at"])
            )
            db.add(new_integration)
        
        db.commit()
        await client.close()
        
        return {"message": "Integração Shopee concluída", "status": "success"}
    except Exception as e:
        await client.close()
        raise HTTPException(status_code=400, detail=str(e))


# ===== SHEIN =====

@router.get("/integrations/shein/connect")
async def shein_connect(tenant_id: UUID):
    """Retorna URL OAuth do Shein"""
    client = SheinClient()
    return {"auth_url": client.get_auth_url(str(tenant_id))}


@router.get("/integrations/shein/callback")
async def shein_callback(code: str, state: str, db: Session = Depends(get_db)):
    """Troca code por access token e salva"""
    try:
        client = SheinClient()
        token_data = await client.exchange_code(code)
        
        # Verificar se já existe integração para este tenant
        existing = db.query(SheinIntegration).filter(
            SheinIntegration.tenant_id == UUID(state)
        ).first()
        
        if existing:
            # Atualizar
            existing.access_token = token_data["access_token"]
            existing.refresh_token = token_data["refresh_token"]
            existing.expires_at = datetime.fromisoformat(token_data["expires_at"])
        else:
            # Criar nova
            new_integration = SheinIntegration(
                tenant_id=UUID(state),
                access_token=token_data["access_token"],
                refresh_token=token_data["refresh_token"],
                expires_at=datetime.fromisoformat(token_data["expires_at"])
            )
            db.add(new_integration)
        
        db.commit()
        await client.close()
        
        return {"message": "Integração Shein concluída", "status": "success"}
    except Exception as e:
        await client.close()
        raise HTTPException(status_code=400, detail=str(e))
