from fastapi import APIRouter, HTTPException, Depends, status, Request, Body, Path
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
from prisma import Prisma
from app.auth.models import SendOTPRequest, VerifyOTPRequest, TokenResponse, MeResponse, MCPServerRequest, MCPServerResponse, MCPServerUpdateRequest
from app.auth.otp_manager import OTPManager
from app.auth.jwt_handler import create_access_token, decode_access_token
from app.auth.send_email import send_email
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.oauth2 import id_token
from google.auth.transport import requests as grequests

router = APIRouter()
otp_manager = OTPManager()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Registration request model
class RegisterRequest(BaseModel):
    name: str
    email: EmailStr

# Register endpoint
@router.post("/register")
async def register_user(
    data: RegisterRequest,
    token: str = Depends(oauth2_scheme)
):
    try:
        print(f"[DEBUG] Registering user: {data.email}, {data.name}")
        
        # Test bypass for development
        if data.email == "test@gmail.com":
            print(f"[DEBUG] Test email bypass - auto-registering as Admin")
            prisma = Prisma()
            await prisma.connect()
            existing = await prisma.user.find_unique(where={"email": data.email})
            if existing:
                await prisma.disconnect()
                return {"message": "Test user already exists", "user": {"id": existing.id, "name": existing.name, "email": existing.email}}
            user = await prisma.user.create(
                data={
                    "name": "Admin",  # Force name to Admin for test user
                    "email": data.email,
                }
            )
            print(f"[DEBUG] Created test user: {user}")
            await prisma.disconnect()
            return {"message": "Test user registration successful", "user": {"id": user.id, "name": user.name, "email": user.email}}
        
        # Decode token and check if it matches the email
        payload = decode_access_token(token)
        print(f"[DEBUG] Token payload: {payload}")
        if payload.get("sub") != data.email:
            print("[DEBUG] Token email does not match registration email.")
            raise HTTPException(status_code=401, detail="Invalid token for this email.")

        prisma = Prisma()
        await prisma.connect()
        existing = await prisma.user.find_unique(where={"email": data.email})
        print(f"[DEBUG] Existing user: {existing}")
        if existing:
            await prisma.disconnect()
            raise HTTPException(status_code=400, detail="Email already registered.")
        user = await prisma.user.create(
            data={
                "name": data.name,
                "email": data.email,
            }
        )
        print(f"[DEBUG] Created user: {user}")
        await prisma.disconnect()
        return {"message": "Registration successful", "user": {"id": user.id, "name": user.name, "email": user.email}}
    except Exception as e:
        print(f"[ERROR] Registration failed: {e}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {e}")

@router.post("/send-otp")
async def send_otp(data: SendOTPRequest):
    # Test bypass for development
    if data.email == "test@gmail.com":
        print(f"[DEBUG] Test email bypass for: {data.email}")
        return {"message": "Test bypass - no OTP needed for test@gmail.com"}
    
    prisma = Prisma()
    await prisma.connect()
    existing = await prisma.user.find_unique(where={"email": data.email})
    await prisma.disconnect()
    if data.purpose == "register":
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered.")
    elif data.purpose == "login":
        if not existing:
            raise HTTPException(status_code=400, detail="Email not registered.")
    else:
        raise HTTPException(status_code=400, detail="Invalid purpose.")
    otp = otp_manager.generate_otp(data.email)
    send_email(data.email, otp)
    return {"message": "OTP sent to email."}

@router.post("/verify-otp", response_model=TokenResponse)
def verify_otp(data: VerifyOTPRequest):
    # Test bypass for development
    if data.email == "test@gmail.com":
        print(f"[DEBUG] Test email bypass - creating token for: {data.email}")
        token = create_access_token({"sub": data.email})
        return TokenResponse(access_token=token)
    
    if not otp_manager.verify_otp(data.email, data.otp):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP.")
    token = create_access_token({"sub": data.email})
    return TokenResponse(access_token=token)

@router.post("/google-login")
async def google_login(request: Request):
    data = await request.json()
    token = data.get("id_token")
    if not token:
        raise HTTPException(status_code=400, detail="Missing Google ID token.")
    try:
        # Verify the token with Google
        idinfo = id_token.verify_oauth2_token(token, grequests.Request())
        email = idinfo.get("email")
        name = idinfo.get("name", "")
        if not email:
            raise HTTPException(status_code=400, detail="Google token missing email.")
        prisma = Prisma()
        await prisma.connect()
        user = await prisma.user.find_unique(where={"email": email})
        if not user:
            user = await prisma.user.create(data={"email": email, "name": name})
        await prisma.disconnect()
        jwt_token = create_access_token({"sub": email})
        return {"access_token": jwt_token, "user": {"id": user.id, "name": user.name, "email": user.email}}
    except Exception as e:
        print(f"[ERROR] Google login failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid Google token.")

@router.get("/me", response_model=MeResponse)
async def get_me(token: str = Depends(oauth2_scheme)):
    try:
        payload = decode_access_token(token)
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token.")
        
        prisma = Prisma()
        await prisma.connect()
        user = await prisma.user.find_unique(where={"email": email})
        
        # Auto-create test user if it doesn't exist
        if not user and email == "test@gmail.com":
            print(f"[DEBUG] Auto-creating test user for: {email}")
            user = await prisma.user.create(
                data={
                    "name": "Admin",
                    "email": email,
                }
            )
            print(f"[DEBUG] Created test user: {user}")
        
        await prisma.disconnect()
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")
        return {"email": user.email, "name": user.name}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")

@router.get("/user/preferred-model")
async def get_preferred_model(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token.")
    prisma = Prisma()
    await prisma.connect()
    user = await prisma.user.find_unique(where={"email": email})
    await prisma.disconnect()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return {"preferredModel": user.preferredModel}

@router.post("/user/preferred-model")
async def set_preferred_model(
    model: str = Body(..., embed=True),
    token: str = Depends(oauth2_scheme)
):
    payload = decode_access_token(token)
    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token.")
    prisma = Prisma()
    await prisma.connect()
    user = await prisma.user.find_unique(where={"email": email})
    if not user:
        await prisma.disconnect()
        raise HTTPException(status_code=404, detail="User not found.")
    updated = await prisma.user.update(
        where={"email": email},
        data={"preferredModel": model}
    )
    await prisma.disconnect()
    return {"preferredModel": updated.preferredModel}

class APIKeyRequest(BaseModel):
    name: str
    provider: str
    value: str

@router.get("/api-keys")
async def list_api_keys(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token.")
    prisma = Prisma()
    await prisma.connect()
    user = await prisma.user.find_unique(where={"email": email})
    if not user:
        await prisma.disconnect()
        raise HTTPException(status_code=404, detail="User not found.")
    keys = await prisma.apikey.find_many(where={"userId": user.id})
    await prisma.disconnect()
    return keys

@router.post("/api-keys")
async def add_api_key(
    req: APIKeyRequest,
    token: str = Depends(oauth2_scheme)
):
    payload = decode_access_token(token)
    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token.")
    prisma = Prisma()
    await prisma.connect()
    user = await prisma.user.find_unique(where={"email": email})
    if not user:
        await prisma.disconnect()
        raise HTTPException(status_code=404, detail="User not found.")
    new_key = await prisma.apikey.create(data={
        "userId": user.id,
        "name": req.name,
        "provider": req.provider,
        "value": req.value
    })
    await prisma.disconnect()
    return new_key

@router.delete("/api-keys/{id}")
async def delete_api_key(
    id: int = Path(...),
    token: str = Depends(oauth2_scheme)
):
    payload = decode_access_token(token)
    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token.")
    prisma = Prisma()
    await prisma.connect()
    user = await prisma.user.find_unique(where={"email": email})
    if not user:
        await prisma.disconnect()
        raise HTTPException(status_code=404, detail="User not found.")
    key = await prisma.apikey.find_unique(where={"id": id})
    if not key or key.userId != user.id:
        await prisma.disconnect()
        raise HTTPException(status_code=404, detail="API key not found.")
    await prisma.apikey.delete(where={"id": id})
    await prisma.disconnect()
    return {"status": "deleted"}

# MCP Server Management Endpoints

@router.get("/mcp-servers")
async def list_mcp_servers(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token.")
    prisma = Prisma()
    await prisma.connect()
    user = await prisma.user.find_unique(where={"email": email})
    if not user:
        await prisma.disconnect()
        raise HTTPException(status_code=404, detail="User not found.")
    servers = await prisma.mcpserver.find_many(where={"userId": user.id})
    await prisma.disconnect()
    return servers

@router.post("/mcp-servers")
async def add_mcp_server(
    req: MCPServerRequest,
    token: str = Depends(oauth2_scheme)
):
    payload = decode_access_token(token)
    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token.")
    prisma = Prisma()
    await prisma.connect()
    user = await prisma.user.find_unique(where={"email": email})
    if not user:
        await prisma.disconnect()
        raise HTTPException(status_code=404, detail="User not found.")
    new_server = await prisma.mcpserver.create(data={
        "userId": user.id,
        "name": req.name,
        "description": req.description,
        "config": req.config
    })
    await prisma.disconnect()
    return new_server

@router.put("/mcp-servers/{id}")
async def update_mcp_server(
    id: int = Path(...),
    req: MCPServerUpdateRequest = Body(...),
    token: str = Depends(oauth2_scheme)
):
    payload = decode_access_token(token)
    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token.")
    prisma = Prisma()
    await prisma.connect()
    user = await prisma.user.find_unique(where={"email": email})
    if not user:
        await prisma.disconnect()
        raise HTTPException(status_code=404, detail="User not found.")
    server = await prisma.mcpserver.find_unique(where={"id": id})
    if not server or server.userId != user.id:
        await prisma.disconnect()
        raise HTTPException(status_code=404, detail="MCP server not found.")
    
    # Build update data only with provided fields
    update_data = {}
    if req.name is not None:
        update_data["name"] = req.name
    if req.description is not None:
        update_data["description"] = req.description
    if req.config is not None:
        update_data["config"] = req.config
    
    updated_server = await prisma.mcpserver.update(
        where={"id": id},
        data=update_data
    )
    await prisma.disconnect()
    return updated_server

@router.delete("/mcp-servers/{id}")
async def delete_mcp_server(
    id: int = Path(...),
    token: str = Depends(oauth2_scheme)
):
    payload = decode_access_token(token)
    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token.")
    prisma = Prisma()
    await prisma.connect()
    user = await prisma.user.find_unique(where={"email": email})
    if not user:
        await prisma.disconnect()
        raise HTTPException(status_code=404, detail="User not found.")
    server = await prisma.mcpserver.find_unique(where={"id": id})
    if not server or server.userId != user.id:
        await prisma.disconnect()
        raise HTTPException(status_code=404, detail="MCP server not found.")
    await prisma.mcpserver.delete(where={"id": id})
    await prisma.disconnect()
    return {"status": "deleted"}
