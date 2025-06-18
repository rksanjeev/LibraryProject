from pydantic import BaseModel, Field
from typing import List, Literal
from datetime import datetime

class BookBase(BaseModel):
    isbn: str = Field(..., description="ISBN number")
    authors: str = Field(..., description="Authors of the book")
    publication_year: int = Field(..., description="Year of publication")
    title: str = Field(..., description="Title of the book")
    language: str = Field(..., description="Language code")
    rental_status: Literal["available", "borrowed"] = Field("available", description="Rental status of the book")

class BookCreate(BookBase):
    pass

class Book(BookBase):
    id: int

    class Config:
        orm_mode = True

class WishlistBase(BaseModel):
    user_id: int = Field(..., description="ID of the user")
    book_ids: List[int] = Field(..., description="List of book IDs in the wishlist")

class Wishlist(WishlistBase):
    id: int
    class Config:
        orm_mode = True

class RentalBase(BaseModel):
    user_id: int = Field(..., description="ID of the user")
    book_id: int = Field(..., description="ID of the book")
    rental_date: datetime = Field(..., description="Date of rental")

class Rental(RentalBase):
    id: int
    class Config:
        orm_mode = True

class RentalRequest(BaseModel):
    user: int = Field(..., description="User ID")
    books: int = Field(..., description="Book ID")