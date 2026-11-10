from typing import Optional
from pydantic import BaseModel

class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    
    class Config:
        from_attributes = True

class MLIntegrationBase(BaseModel):
    tenant_id: str
    access_token: Optional[str] = None

class MLIntegration(MLIntegrationBase):
    id: int
    
    class Config:
        from_attributes = True

class SuggestionCreate(BaseModel):
    """Schema para criar sugestões de otimização"""
    title: str
    description: str
    potential_impact: Optional[str] = None

class Suggestion(SuggestionCreate):
    id: int
    tenant_id: str
    
    class Config:
        from_attributes = True
