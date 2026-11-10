from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base
from app.crypto_tokens import EncryptedText

def gen_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=gen_uuid)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    tiktok_accounts = relationship("TikTokAccount", back_populates="user")

class TikTokAccount(Base):
    __tablename__ = "tiktok_accounts"
    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    shop_id = Column(String, nullable=False)
    shop_name = Column(String)
    access_token = Column(EncryptedText, nullable=False)
    refresh_token = Column(EncryptedText)
    token_expires_at = Column(DateTime)
    shop_cipher = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="tiktok_accounts")

class Product(Base):
    __tablename__ = "products"
    id = Column(String, primary_key=True, default=gen_uuid)
    tiktok_account_id = Column(String, ForeignKey("tiktok_accounts.id"))
    tiktok_product_id = Column(String, nullable=False)
    name = Column(String)
    price = Column(Float)
    cost = Column(Float)
    stock = Column(Integer, default=0)
    status = Column(String)
    updated_at = Column(DateTime, default=datetime.utcnow)

class Order(Base):
    __tablename__ = "orders"
    id = Column(String, primary_key=True, default=gen_uuid)
    tiktok_account_id = Column(String, ForeignKey("tiktok_accounts.id"))
    tiktok_order_id = Column(String, nullable=False)
    status = Column(String)
    total = Column(Float)          # ← era total_amount no model, mas o frontend usa .total
    total_amount = Column(Float)   # ← mantido para compatibilidade
    created_at = Column(DateTime, default=datetime.utcnow)

class Recommendation(Base):
    __tablename__ = "recommendations"
    id = Column(String, primary_key=True, default=gen_uuid)
    tiktok_account_id = Column(String, ForeignKey("tiktok_accounts.id"))
    product_id = Column(String, ForeignKey("products.id"))
    type = Column(String)
    rule_triggered = Column(String)
    suggested_value = Column(Float)
    ai_justification = Column(Text)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
class BlingIntegration(Base):
    __tablename__ = "bling_integrations"
    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    access_token = Column(Text)
    refresh_token = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

