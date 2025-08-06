from pydantic import BaseModel, EmailStr, constr
from typing import Annotated, Optional, Dict, Any

class SendOTPRequest(BaseModel):
    email: EmailStr
    purpose: str  # 'register' or 'login'

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: Annotated[str, constr(min_length=6, max_length=6, pattern=r"^\d{6}$")]

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class MeResponse(BaseModel):
    email: EmailStr
    name: str

# MCP Server Management Models
class MCPServerRequest(BaseModel):
    name: str
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None

class MCPServerResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    config: Dict[str, Any]
    createdAt: str

class MCPServerUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None

# API Key Management Models
class APIKeyRequest(BaseModel):
    name: str
    provider: str
    value: str

class APIKeyResponse(BaseModel):
    id: int
    name: str
    provider: str
    value: str  # This will be masked in the response
    createdAt: str

class APIKeyUpdateRequest(BaseModel):
    name: Optional[str] = None
    provider: Optional[str] = None
    value: Optional[str] = None
