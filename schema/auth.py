from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    access_token: str = Field(..., description="The access token for the user")
    refresh_token: str = Field(..., description="The refresh token for the user")
    token_type: str = Field(..., description="The type of the token, typically 'bearer'")

class TokenPayload(BaseModel):
    sub: str | None= None
    exp: int = 0

class ResendTokenRequest(BaseModel):
    email: EmailStr = Field(..., description="The email address to resend the token to")
    username: str = Field(..., description="The username of the user requesting the token resend")
    password: str = Field(..., min_length=8, description="The user's password for verification")
