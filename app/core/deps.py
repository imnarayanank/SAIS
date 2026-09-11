"""Authentication dependencies for local JWT and Supabase OAuth sessions."""
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .security import decode_access_token
from ..models.user import User

security = HTTPBearer(auto_error=True)


def _supabase_user(access_token: str) -> dict | None:
    """Validate a Supabase access token through Supabase Auth's user endpoint."""
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        return None
    request = Request(
        f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/user",
        headers={
            "apikey": settings.SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {access_token}",
        },
    )
    try:
        with urlopen(request, timeout=8) as response:
            if response.status != 200:
                return None
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, ValueError):
        return None


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Accept local SAIS JWTs and Supabase OAuth bearer tokens."""
    token = credentials.credentials
    payload = decode_access_token(token)
    if payload and payload.get("sub"):
        user = db.query(User).filter(User.user_id == int(payload["sub"])).first()
        if user:
            return user

    auth_user = _supabase_user(token)
    if auth_user and auth_user.get("email"):
        email = auth_user["email"].lower()
        metadata = auth_user.get("user_metadata") or {}
        name = metadata.get("full_name") or metadata.get("name") or email.split("@")[0]
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(name=name[:100], email=email, password_hash=None)
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token",
        headers={"WWW-Authenticate": "Bearer"},
    )
