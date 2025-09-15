from fastapi import APIRouter, HTTPException
from fastapi import Depends
from ..schemas import LoginRequest, Token
from ..utils import jwt as jwt_utils

# initialize django auth
from django.contrib.auth import authenticate

router = APIRouter()

@router.post("/login", response_model=Token)
def login(data: LoginRequest):
    user = authenticate(username=data.username, password=data.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    # Build token payload with useful info
    payload = {
        "user_id": user.id,
        "username": user.username,
        "is_org_admin": bool(getattr(user, "is_org_admin", False))
    }
    token = jwt_utils.create_access_token(payload)
    return {"access_token": token, "token_type": "bearer"}
