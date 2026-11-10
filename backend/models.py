import uuid
from sqlalchemy import Column, String, Text, DateTime, Integer, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from database import Base
from datetime import datetime


class Suggestion(Base):
    __tablename__ = "suggestions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    channel_id = Column(UUID(as_uuid=True), nullable=True)
    
    suggestion_type = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(UUID(as_uuid=True), nullable=True)
    
    priority = Column(String(20), default="medium")
    estimated_impact = Column(String(100), nullable=True)
    status = Column(String(50), default="pending")
    generated_by = Column(String(50), default="rules_engine")
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class MLIntegration(Base):
    """Modelo para armazenar integração com Mercado Livre"""
    __tablename__ = "ml_integrations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, unique=True)
    
    access_token = Column(String(500), nullable=False)
    refresh_token = Column(String(500), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    
    seller_id = Column(String(100), nullable=True)
    seller_nickname = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class ApiUsage(Base):
    """Modelo para rastrear uso da API (tokens Claude, chamadas API)"""
    __tablename__ = "api_usage"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    
    service = Column(String(50), nullable=False)  # "claude", "mercadolivre", etc
    endpoint = Column(String(255), nullable=False)
    
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    
    cost = Column(Float, nullable=True)
    status = Column(String(20), default="success")
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())

class ShopeeIntegration(Base):
    """Modelo para armazenar integração com Shopee"""
    __tablename__ = "shopee_integrations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, unique=True)

    access_token = Column(String(500), nullable=False)
    refresh_token = Column(String(500), nullable=False)
    expires_at = Column(DateTime, nullable=False)

    shop_id = Column(String(100), nullable=True)
    shop_name = Column(String(255), nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class SheinIntegration(Base):
    """Modelo para armazenar integração com Shein"""
    __tablename__ = "shein_integrations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, unique=True)

    access_token = Column(String(500), nullable=False)
    refresh_token = Column(String(500), nullable=False)
    expires_at = Column(DateTime, nullable=False)

    seller_id = Column(String(100), nullable=True)
    seller_name = Column(String(255), nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
