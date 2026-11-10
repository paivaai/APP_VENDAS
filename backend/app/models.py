"""Modelos. Hierarquia: Tenant (cobrado) -> Store (1 por telefone/terminal)
-> Channel (ML / Shopee / TikTok) -> Agent.

TODO: reconciliar com o models.py real da VPS (colunas podem diferir).
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON, Text, Float
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


def _uuid():
    return str(uuid.uuid4())


class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String, nullable=False)
    cnpj = Column(String, unique=True, nullable=True)
    status = Column(String, default="onboarding")  # onboarding, active, suspended
    created_at = Column(DateTime, default=datetime.utcnow)


class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=_uuid)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=True)
    email = Column(String, unique=True, nullable=False)  # vai no `sub` do JWT
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Store(Base):
    __tablename__ = "stores"
    id = Column(String, primary_key=True, default=_uuid)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    name = Column(String, nullable=False)


class Channel(Base):
    __tablename__ = "channels"
    id = Column(String, primary_key=True, default=_uuid)
    store_id = Column(String, ForeignKey("stores.id"), nullable=False)
    marketplace = Column(String, nullable=False)  # mercado_livre, shopee, tiktok, shein
    external_id = Column(String, nullable=True)


class BlingIntegration(Base):
    __tablename__ = "bling_integrations"
    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    access_token = Column(Text, nullable=False)   # TODO: criptografar (TOKEN_ENCRYPTION_KEY)
    refresh_token = Column(Text, nullable=False)  # TODO: criptografar
    expires_at = Column(DateTime, nullable=True)


class ProductSuggestion(Base):
    __tablename__ = "product_suggestions"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    marketplace = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending, ready_to_register, registered, rejected, failed
    criticality = Column(String, default="normal")  # normal, alta, critica
    raw_data = Column(JSON, nullable=False)
    normalized_data = Column(JSON, nullable=True)
    missing_fields = Column(JSON, nullable=True)
    image_urls = Column(JSON, nullable=True)
    whatsapp_message_id = Column(String, nullable=True)
    decided_via = Column(String, nullable=True)  # whatsapp, dashboard, auto
    marketplace_product_id = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ApiUsage(Base):
    """Consumo de tokens da Claude API por tenant (base da cobrança)."""
    __tablename__ = "api_usage"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    agent = Column(String, nullable=False)
    model = Column(String, nullable=False)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
