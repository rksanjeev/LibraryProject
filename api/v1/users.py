from fastapi import APIRouter, status
from services.email import send_email 
from fastapi import  Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from db import get_session
from schema.users import LoggedInUser
import os
from db.models.books import WishlistModel, BookModel
from schema.books import Wishlist, BookBase
from services.auth import generate_confirmation_token, get_current_user
from typing import List, Optional

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
def add_to_wishlist(book_id: int, user: LoggedInUser = Depends(get_current_user), db: Session = Depends(get_session)):
    book = db.query(BookModel).filter(BookModel.id == book_id).first()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    wishlist = db.query(WishlistModel).filter(WishlistModel.user_id == user.id).first()
    if not wishlist:
        wishlist = WishlistModel(user_id=user.id, books=[])
        db.add(wishlist)
        db.commit()
        db.refresh(wishlist)
    if book not in wishlist.books:
        wishlist.books.append(book)
        db.commit()
    return {"message": "Book added to wishlist successfully"}

@router.delete("/wishlist/{book_id}")
def remove_from_wishlist(book_id: int, user: LoggedInUser = Depends(get_current_user), db: Session = Depends(get_session)):
    wishlist = db.query(WishlistModel).filter(WishlistModel.user_id == user.id).first()
    if not wishlist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wishlist not found for user")
    book = db.query(BookModel).filter(BookModel.id == book_id).first()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    if book in wishlist.books:
        wishlist.books.remove(book)
        db.commit()
        return {"message": "Book removed from wishlist successfully"}
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not in wishlist")

@router.get("/search", response_model=List[BookBase], tags=["search"])
def search_books(
    author: Optional[str] = None,
    title: Optional[str] = None,
    db: Session = Depends(get_session)
):
    query = db.query(BookModel)
    if author:
        query = query.filter(BookModel.authors.ilike(f"%{author}%"))
    if title:
        query = query.filter(BookModel.title.ilike(f"%{title}%"))
    books = query.all()
    result = []
    for book in books:
        rental_status = str(getattr(book.rental_status, 'value', book.rental_status))
        if rental_status not in ("available", "borrowed"):
            rental_status = "available"
        result.append(BookBase(
            isbn=getattr(book, "isbn"),
            authors=getattr(book, "authors"),
            publication_year=getattr(book, "publication_year"),
            title=getattr(book, "title"),
            language=getattr(book, "language"),
            rental_status=rental_status  # type: ignore
        ))
    return result


@router.post("/request-staff-access")
def request_staff_access(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_session),
    user: LoggedInUser = Depends(get_current_user)
):
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    token = generate_confirmation_token(user.email)
    subject = "Staff Access Request"
    body = f"User {user.username} has requested staff access. Please review their request at {os.getenv('HOST')}:{os.getenv('PORT')}/api/v1/admin/confirm-staff-access?token={token}."
    background_tasks.add_task(send_email, subject=subject, body=body, to=os.getenv("ADMIN_EMAIL"))
    return {"message": f"Staff access request for {user.username} has been sent."}
