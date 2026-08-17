from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.auth import UserCreate, UserLogin, UserOut, Token
from app.utils.security import verify_password, get_password_hash, create_access_token, decode_access_token

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation requires administrator privileges"
        )
    return current_user

def to_user_out(user: User) -> UserOut:
    if hasattr(UserOut, "model_validate"):
        return UserOut.model_validate(user)
    return UserOut.from_orm(user)

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Hash password and create user
    hashed_pwd = get_password_hash(user_data.password)
    user = User(
        full_name=user_data.full_name,
        email=user_data.email.lower(),
        hashed_password=hashed_pwd,
        role=user_data.role if user_data.role in ["user", "admin"] else "user"
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Generate access token
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role, "user_id": user.id}
    )
    
    user_out = to_user_out(user)
    return Token(access_token=access_token, token_type="bearer", user=user_out)

@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_data.email.lower()).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )
    
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role, "user_id": user.id}
    )
    
    user_out = to_user_out(user)
    return Token(access_token=access_token, token_type="bearer", user=user_out)

@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
