from fastapi import Depends, HTTPException, Header
from typing import Optional
from .utils import jwt as jwt_utils
from django.contrib.auth import get_user_model

User = get_user_model()

def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization header")
    token = authorization.split(" ", 1)[1]
    payload = jwt_utils.decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user_id = payload.get("user_id")   
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        raise HTTPException(status_code=401, detail="User not found")
    return user
