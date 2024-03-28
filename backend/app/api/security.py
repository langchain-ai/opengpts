import datetime
import os
import jwt

from fastapi import HTTPException

# Get the secret key from environment variable
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY not set on your environment.")

# Token expiration time (1 hour)
TOKEN_EXPIRATION = datetime.timedelta(hours=1)

def create_token(username: str) -> str:
    """Create JWT token."""
    payload = {
        'username': username,
        'exp': datetime.datetime.utcnow() + TOKEN_EXPIRATION
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token

def verify_token(token: str) -> dict:
    """Verify JWT token and return payload."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=403, detail="Could not validate credentials")
