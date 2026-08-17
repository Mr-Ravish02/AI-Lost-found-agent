import hashlib
import json
import base64
from datetime import datetime, timedelta, timezone
from typing import Optional
from app.config import settings


try:
    from jose import JWTError, jwt
except ImportError:
    try:
        import jwt
        JWTError = Exception
    except ImportError:
        # Fallback simple base64 token helper for local dev testing if packages aren't installed yet
        class LocalJWT:
            @staticmethod
            def encode(payload, secret, algorithm=None):
                data = json.dumps(payload).encode('utf-8')
                return base64.urlsafe_b64encode(data).decode('utf-8')
            
            @staticmethod
            def decode(token, secret, algorithms=None):
                data = base64.urlsafe_b64decode(token.encode('utf-8'))
                return json.loads(data.decode('utf-8'))
        
        jwt = LocalJWT
        JWTError = Exception

try:
    import bcrypt
    def get_password_hash(password: str) -> str:
        pwd_bytes = password.encode('utf-8')[:72]
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')

    def verify_password(plain_password: str, hashed_password: str) -> bool:
        pwd_bytes = plain_password.encode('utf-8')[:72]
        try:
            return bcrypt.checkpw(pwd_bytes, hashed_password.encode('utf-8'))
        except Exception:
            return False
except ImportError:
    # Fallback hashlib sha256 for local dev testing
    def get_password_hash(password: str) -> str:
        return hashlib.sha256(password.encode('utf-8')).hexdigest()
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return get_password_hash(plain_password) == hashed_password



def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None
