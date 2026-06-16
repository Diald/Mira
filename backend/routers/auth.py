import httpx
from fastapi import APIRouter, HTTPException, status

from backend.config import get_settings
from backend.schemas import LoginRequest, SignupRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


async def _supabase_password_request(path: str, email: str, password: str) -> TokenResponse:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_anon_key:
        raise HTTPException(status_code=500, detail="Supabase Auth is not configured")

    url = f"{settings.supabase_url.rstrip('/')}/auth/v1/{path}"
    headers = {"apikey": settings.supabase_anon_key, "Authorization": f"Bearer {settings.supabase_anon_key}"}
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(url, json={"email": email, "password": password}, headers=headers)
    if response.status_code >= 400:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed")
    data = response.json()
    token = data.get("access_token") or data.get("session", {}).get("access_token")
    if not token:
        raise HTTPException(status_code=502, detail="Supabase did not return an access token")
    return TokenResponse(access_token=token)


@router.post("/signup", response_model=TokenResponse)
async def signup(payload: SignupRequest) -> TokenResponse:
    return await _supabase_password_request("signup", payload.email, payload.password)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest) -> TokenResponse:
    return await _supabase_password_request("token?grant_type=password", payload.email, payload.password)
