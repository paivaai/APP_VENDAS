# Endpoints para o painel admin
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from database import get_db
from models import Tenant, MLIntegration, ShopeeIntegration, SheinIntegration, ApiUsage
from sqlalchemy import func

router = APIRouter(prefix="/admin", tags=["admin"])

ADMIN_SECRET = "admin-secret-key"  # Deve ser uma env var

def verify_admin_key(x_admin_key: str = None):
    """Verifica se a chave de admin é válida"""
    if x_admin_key != ADMIN_SECRET:
        raise HTTPException(status_code=401, detail="Chave de admin inválida")
    return True

# ===== TENANTS =====

@router.get("/tenants")
async def list_tenants(db: Session = Depends(get_db), _: bool = Depends(verify_admin_key)):
    """Lista todos os clientes (tenants)"""
    tenants = db.query(Tenant).all()
    return [
        {
            "id": str(t.id),
            "name": t.name,
            "email": t.email,
            "status": t.status,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in tenants
    ]


@router.get("/tenants/{tenant_id}")
async def get_tenant(tenant_id: UUID, db: Session = Depends(get_db), _: bool = Depends(verify_admin_key)):
    """Obtém detalhes de um cliente"""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant não encontrado")
    
    return {
        "id": str(tenant.id),
        "name": tenant.name,
        "email": tenant.email,
        "status": tenant.status,
        "created_at": tenant.created_at.isoformat() if tenant.created_at else None,
    }


@router.post("/tenants")
async def create_tenant(name: str, email: str, db: Session = Depends(get_db), _: bool = Depends(verify_admin_key)):
    """Cria um novo cliente"""
    new_tenant = Tenant(name=name, email=email, status="active")
    db.add(new_tenant)
    db.commit()
    db.refresh(new_tenant)
    
    return {
        "id": str(new_tenant.id),
        "name": new_tenant.name,
        "email": new_tenant.email,
        "status": new_tenant.status,
    }


@router.put("/tenants/{tenant_id}")
async def update_tenant(tenant_id: UUID, name: str = None, status: str = None, db: Session = Depends(get_db), _: bool = Depends(verify_admin_key)):
    """Edita um cliente"""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant não encontrado")
    
    if name:
        tenant.name = name
    if status:
        tenant.status = status
    
    db.commit()
    db.refresh(tenant)
    
    return {
        "id": str(tenant.id),
        "name": tenant.name,
        "email": tenant.email,
        "status": tenant.status,
    }


# ===== USAGE =====

@router.get("/tenants/{tenant_id}/usage")
async def get_tenant_usage(tenant_id: UUID, db: Session = Depends(get_db), _: bool = Depends(verify_admin_key)):
    """Obtém consumo de tokens de um tenant"""
    usage = db.query(
        ApiUsage.service,
        func.sum(ApiUsage.input_tokens).label("input_tokens"),
        func.sum(ApiUsage.output_tokens).label("output_tokens"),
        func.sum(ApiUsage.total_tokens).label("total_tokens"),
        func.count(ApiUsage.id).label("requests")
    ).filter(ApiUsage.tenant_id == tenant_id).group_by(ApiUsage.service).all()
    
    return [
        {
            "service": row[0],
            "input_tokens": row[1] or 0,
            "output_tokens": row[2] or 0,
            "total_tokens": row[3] or 0,
            "requests": row[4]
        }
        for row in usage
    ]


# ===== INTEGRATIONS =====

@router.get("/tenants/{tenant_id}/integrations")
async def get_tenant_integrations(tenant_id: UUID, db: Session = Depends(get_db), _: bool = Depends(verify_admin_key)):
    """Obtém integrações conectadas de um tenant"""
    result = {
        "mercado_livre": None,
        "shopee": None,
        "shein": None,
    }
    
    ml = db.query(MLIntegration).filter(MLIntegration.tenant_id == tenant_id).first()
    if ml:
        result["mercado_livre"] = {
            "connected": True,
            "seller_id": ml.seller_id,
            "seller_nickname": ml.seller_nickname,
            "expires_at": ml.expires_at.isoformat() if ml.expires_at else None,
        }
    
    shopee = db.query(ShopeeIntegration).filter(ShopeeIntegration.tenant_id == tenant_id).first()
    if shopee:
        result["shopee"] = {
            "connected": True,
            "shop_id": shopee.shop_id,
            "shop_name": shopee.shop_name,
            "expires_at": shopee.expires_at.isoformat() if shopee.expires_at else None,
        }
    
    shein = db.query(SheinIntegration).filter(SheinIntegration.tenant_id == tenant_id).first()
    if shein:
        result["shein"] = {
            "connected": True,
            "seller_id": shein.seller_id,
            "seller_name": shein.seller_name,
            "expires_at": shein.expires_at.isoformat() if shein.expires_at else None,
        }
    
    return result
