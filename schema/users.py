from pydantic import BaseModel, EmailStr, Field

class UserBase(BaseModel):
    email: EmailStr = Field(..., description="The user's email address")
    username: str = Field(..., description="The user's first name")
    

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="The user's password")


class LoggedInUser(UserBase):
    id: int = Field(..., description="The unique identifier of the user")
    is_active: bool = Field(..., description="Indicates if the user is active")
    

class LoggedInStaffUser(LoggedInUser):
    is_staff: bool = Field(..., description="Indicates if the user has staff privileges")