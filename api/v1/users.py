from fastapi import APIRouter
from services.email import send_email 
from fastapi import  Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from db import get_session
from schema.users import LoggedInUser
from services.auth import get_current_user
import os
from db.models.books import WishlistModel, BookModel
from schema.books import Wishlist, Book
from fastapi import status
from db.models.users import UserModel


router = APIRouter(prefix="/user")


@router.get("/wishlist", response_model=Wishlist)
def get_user_wislist(user: LoggedInUser = Depends(get_current_user), db: Session = Depends(get_session)):
    wishlist = db.query(WishlistModel).filter(WishlistModel.user_id == user.id).first()
    if not wishlist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wishlist not found for user")
    book_ids = [book.id for book in wishlist.books]
    return Wishlist(
        id=wishlist.__dict__["id"],
        user_id=wishlist.__dict__["user_id"],
        book_ids=book_ids
    )

@router.post("/wishlist")
def add_to_wishlist(book_id: int, user: LoggedInUser = Depends(get_current_user),):
    """
    Add an item to the user's wishlist.
    """
    # Placeholder for actual implementation
    return {"message": "Item added to wishlist successfully"}

@router.delete("/wishlist/{book_id: int}")
async def remove_from_wishlist(book_id: int):
    """
    Remove an item from the user's wishlist.
    """
    # Placeholder for actual implementation
    return {"message": "Item removed from wishlist successfully"}

@router.get("/search", tags=["search"])
async def search_books(autor: str | None=None, title: str | None=None):
    """
    Search for items based on a query.
    """
    # Placeholder for actual implementation
    return {"message": f"Search results for'"}


@router.post("/request-staff-access")
def request_staff_access(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_session),
    user: LoggedInUser = Depends(get_current_user)
):
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    subject = "Staff Access Request"
    body = f"User {user.username} has requested staff access."
    background_tasks.add_task(send_email, subject=subject, body=body, to=os.getenv("ADMIN_EMAIL"))
    return {"message": f"Staff access request for {user.username} has been sent."}
