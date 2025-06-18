import os
import asyncio
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from db import get_session
from schema.users import UserCreate
from services.auth import register_user, generate_confirmation_token, confirm_email_token, resend_confirmation_token, authenticate_user
from services.email import send_email
from schema.auth import ResendTokenRequest, Token


router = APIRouter(prefix="/auth")

@router.post('/login', summary="Create access and refresh tokens for user", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_session)):
    access_token, refresh_token = authenticate_user(
        username=form_data.username,
        password=form_data.password,
        session=db
    )
    if not access_token or not refresh_token:
        raise HTTPException(status_code=401, detail="Invalid credentials")    

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.get("/confirm-email")
def confirm_email_route(token: str, db: Session = Depends(get_session)):
    try:
        user = confirm_email_token(token, db)
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    return {"msg": "Email confirmed. You can now log in."}


@router.post("/register")
def register(user: UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_session)):
    registered_user = register_user(user, db)
    if not register_user:
        raise HTTPException(status_code=400, detail="User registration failed.")
    token = generate_confirmation_token(str(registered_user.email))
    subject = "Confirm your email"
    body = f"Please confirm your email by clicking the link: {os.getenv('HOST')}: {os.getenv('PORT')}/api/v1/auth/confirm-email?token={token}"
    background_tasks.add_task(send_email, subject=subject, body=body, to=str(registered_user.email))
    return {"message": f"User {registered_user.username} registered successfully. Please check your email for confirmation."}


@router.post("/resend-confirmation")
def resend_confirmation_token_request(
    resend_request: ResendTokenRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_session)
):
    token = resend_confirmation_token(username=resend_request.username, password=resend_request.password, email=str(resend_request.email), session=db)
    subject = "Confirm your email"
    body = f"Please confirm your email by clicking the link: {os.getenv('HOST')}: {os.getenv('PORT')}/api/v1/auth/confirm-email?token={token}"
    background_tasks.add_task(send_email, subject=subject, body=body, to=str(resend_request.email))
    return {"message": f"Confirmation email sent to {resend_request.email}. Please check your inbox."}
    