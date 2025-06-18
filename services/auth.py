import os
from datetime import datetime, timedelta, timezone
from typing import Union, Any
from jose import jwt
from jose.exceptions import JWTError
from itsdangerous import URLSafeTimedSerializer
from fastapi import HTTPException, Depends
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from schema.users import UserCreate
from sqlalchemy.orm import Session
from sqlalchemy.future import select
from db import get_session
from db.models.users import UserModel
from schema.auth import TokenPayload
from schema.users import LoggedInUser, LoggedInStaffUser
from pydantic import ValidationError
from services.logger import setup_logger


logger = setup_logger(__name__)

reuseable_oauth = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    scheme_name="JWT"
)

SECRET_KEY = os.environ.get("SECRET_KEY", "default_secret_key")
SALTPASSWORD = os.environ.get("SALTPASSWORD", "default_salt")
ALGORITHM = os.environ.get("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", 30)
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "default-jwt-secret")
JWT_REFRESH_SECRET_KEY = os.environ.get("JWT_REFRESH_SECRET_KEY", "default-jwt-refresh-secret")
REFRESH_TOKEN_EXPIRE_MINUTES = os.environ.get("REFRESH_TOKEN_EXPIRE_MINUTES", 3000)
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    """
    return bcrypt_context.hash(password)

def register_user(user: UserCreate, session: Session):
    existing_user = session.query(UserModel).filter(UserModel.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    user.password = hash_password(user.password)
    new_user = UserModel(**user.model_dump())

    session.add(new_user)
    session.commit()
    return new_user


def generate_confirmation_token(email: str) -> str:
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    return serializer.dumps(email, salt=SALTPASSWORD)

def confirm_token(token: str, expiration=3600) -> str:
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    return serializer.loads(token, salt=SALTPASSWORD)


def confirm_email_token(token: str, session: Session):
    try:
        email = confirm_token(token)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = session.query(UserModel).filter(UserModel.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    setattr(user, "is_active", True)
    session.add(user)
    session.commit()
    return user

def resend_confirmation_token(username: str, email: str, password: str, session: Session):
    user = session.query(UserModel).filter(
        UserModel.username == username,
        UserModel.email == email
    ).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if getattr(user, "is_active", False):
        raise HTTPException(status_code=400, detail="Email already confirmed")
    
    if not bcrypt_context.verify(password, getattr(user, "password", "")):
        raise HTTPException(status_code=400, detail="Incorrect password")

    token = generate_confirmation_token(getattr(user, "email"))
    logger.debug(f"Resend token: {token}")  # For debugging purposes, remove in production
    return token


def confirm_staff_token(token: str, session: Session):
    try:
        email = confirm_token(token)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = session.query(UserModel).filter(UserModel.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    setattr(user, "is_staff", True)  # Fixed typo in is_staff
    session.add(user)
    session.commit()
    return user


def create_access_token(subject: Union[str, Any], expires_delta: int = int(ACCESS_TOKEN_EXPIRE_MINUTES)) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_delta) 
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, JWT_ALGORITHM)
    return encoded_jwt

def create_refresh_token(subject: Union[str, Any], expires_delta: int = int(REFRESH_TOKEN_EXPIRE_MINUTES)) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_delta)
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, JWT_REFRESH_SECRET_KEY, JWT_ALGORITHM)
    return encoded_jwt

def authenticate_user(username: str, password: str, session: Session):
    logger.info(f"Authenticating user: {username}")
    logger.info(f"Password provided: {password}")  # For debugging purposes, remove in production
    user = session.query(UserModel).filter(UserModel.email == username).first()
    
    if not user or not bcrypt_context.verify(password, getattr(user, "password")):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    if not getattr(user, "is_active", False):
        raise HTTPException(status_code=400, detail="Email not confirmed")

    access_token = create_access_token(subject=user.email)
    refresh_token = create_refresh_token(subject=user.email)

    logger.debug(f"User {user.email} logged in successfully.")
    # For debugging purposes, remove in production
    return access_token, refresh_token

def get_current_user(token: str = Depends(reuseable_oauth), session: Session = Depends(get_session)) -> LoggedInUser:
    try:
        payload = jwt.decode(
            token, key=JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM]
        )
        token_data = TokenPayload(**payload)

        if datetime.fromtimestamp(token_data.exp) < datetime.now():
            raise HTTPException(
                status_code = 401,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except(JWTError, ValidationError):
        raise HTTPException(
            status_code=403,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = session.query(UserModel).filter(UserModel.email == token_data.sub).first()
    if user is None:
        raise HTTPException(
            status_code=404,
            detail="Could not find user",
        )
    logged_in_user = LoggedInUser(
    id=int(user.id),
    username=str(user.username),
    email=str(user.email),
    is_active=bool(user.is_active)  
    )
    return logged_in_user

def get_current_staff_user(token: str = Depends(reuseable_oauth), session: Session = Depends(get_session)) -> LoggedInStaffUser:
    try:
        payload = jwt.decode(
            token, JWT_SECRET_KEY, algorithms=[ALGORITHM]
        )
        token_data = TokenPayload(**payload)

        if datetime.fromtimestamp(token_data.exp) < datetime.now():
            raise HTTPException(
                status_code=401,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=403,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = session.query(UserModel).filter(UserModel.email == token_data.sub).first()
    if user is None or not getattr(user, "is_staff", False):
        raise HTTPException(
            status_code=404,
            detail="Could not find staff user",
        )
    logged_in_user = LoggedInStaffUser(
    id=int(user.id),
    username=str(user.username),
    email=str(user.email),
    is_active=bool(user.is_active),
    is_staff=bool(user.is_staff)
    )
    return logged_in_user

