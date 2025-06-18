import os
import csv
from fastapi import BackgroundTasks, APIRouter
from fastapi import UploadFile, File
from db import get_session
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException
from services.auth import confirm_staff_token, get_current_staff_user
from schema.users import LoggedInStaffUser
from schema.books import BookCreate, Rental, RentalRequest
from db.models.books import RentalModel, BookModel, WishlistModel, RentalStatusEnum
from db.models.users import UserModel
from services.email import send_email
from datetime import timedelta, datetime, timezone
from fastapi import status


router = APIRouter(prefix="/admin", tags=["admin"])

BOOK_RENTAL_DUE_DAYS = os.environ.get("BOOK_RENTAL_DUE_DAYS", 30) # Default rental period in days

@router.get("/confirm-staff-access")
def confirm_staff_access(token: str, db: Session = Depends(get_session)):
    try:
        user = confirm_staff_token(token, db)
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    return {"msg": "Email confirmed. You can now log in."}

@router.post("/rental/return")
def return_rental(
    data: RentalRequest,
    background_tasks: BackgroundTasks,
    staff_user: LoggedInStaffUser = Depends(get_current_staff_user),
    db: Session = Depends(get_session)
):
    if not staff_user.is_staff:
        raise HTTPException(status_code=403, detail="Not authorized: staff only")
    user_id = data.user
    book_id = data.books
    # Find and delete the rental record
    rental = db.query(RentalModel).filter_by(user_id=user_id, book_id=book_id).first()
    if not rental:
        raise HTTPException(status_code=404, detail="Rental record not found for this user and book")
    db.delete(rental)
    # Mark the book as available
    book = db.query(BookModel).filter(BookModel.id == book_id).first()
    if book:
        book.rental_status = RentalStatusEnum.available.value
    db.commit()
    # List all users who have wishlisted this book
    wishlists = db.query(WishlistModel).filter(WishlistModel.books.any(id=book_id)).all()
    users = []
    for wishlist in wishlists:
        user = db.query(UserModel).filter(UserModel.id == wishlist.user_id).first()
        if user and hasattr(user, 'email'):
            users.append(user.email)
    if users:
        subject = f"Book '{book.title}' is now available"
        body = f"The book '{book.title}' is now available for rental. You can rent it from the library."
        for email in users:
            background_tasks.add_task(send_email, subject=subject, body=body, to=email)
    return {
        "message": "Rental returned, book marked as available.",
    }

@router.post("/rental/extend")
def extend_rental(
    data: RentalRequest,
    background_tasks: BackgroundTasks,
    staff_user: LoggedInStaffUser = Depends(get_current_staff_user),
    db: Session = Depends(get_session)
):
    if not staff_user.is_staff:
        raise HTTPException(status_code=403, detail="Not authorized: staff only")
    user_id = data.user
    book_id = data.books
    rental = db.query(RentalModel).filter_by(user_id=user_id, book_id=book_id).first()
    if not rental:
        raise HTTPException(status_code=404, detail="Rental record not found for this user and book")
    due_days = int(os.environ.get("BOOK_RENTAL_DUE_DAYS", 30))
    new_due_date = rental.rental_date + timedelta(days=due_days)
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    book = db.query(BookModel).filter(BookModel.id == book_id).first()
    if not user or not book:
        raise HTTPException(status_code=404, detail="User or Book not found")
    subject = f"Book Rental Extended: {book.title}"
    body = (
        f"Dear {user.username},\n\n"
        f"Your rental for the book '{book.title}' (ID: {book.id}) has been extended.\n"
        f"New due date: {new_due_date.strftime('%Y-%m-%d')}.\n\nHappy reading!"
    )
    background_tasks.add_task(send_email, subject=subject, body=body, to=str(user.email))
    return {"message": "Rental due date extension notification sent.", "new_due_date": new_due_date.strftime('%Y-%m-%d')}

@router.get("/rental/report")
async def rental_report(staff_user: LoggedInStaffUser = Depends(get_current_staff_user), db :Session = Depends(get_session),username: int | None = None):
    """
    Generate a rental report for an admin.
    """
    # Placeholder for actual implementation
    if username:
        return {"message": f"Rental report for user {username}"}
    return {"message": "Rental report generated successfully"}

@router.get("/rental/report")
def rental_report_all(
    staff_user: LoggedInStaffUser = Depends(get_current_staff_user),
    db: Session = Depends(get_session)
):
    if not staff_user.is_staff:
        raise HTTPException(status_code=403, detail="Not authorized: staff only")
    due_days = int(BOOK_RENTAL_DUE_DAYS)
    report = []
    books = db.query(BookModel).all()
    for book in books:
        rental = db.query(RentalModel).filter(RentalModel.book_id == book.id).first()
        if rental:
            user = db.query(UserModel).filter(UserModel.id == rental.user_id).first()
            rented_on = rental.rental_date
            if hasattr(rented_on, 'to_pydatetime'):
                rented_on = rented_on.to_pydatetime()
            due_date = rented_on + timedelta(days=due_days)
            today = datetime.now(timezone.utc)
            if hasattr(due_date, 'to_pydatetime'):
                due_date = due_date.to_pydatetime()
            # Ensure both are Python datetime objects
            from datetime import datetime as dt
            if isinstance(today, dt) and isinstance(due_date, dt):
                past_due_days = (today - due_date).days if today > due_date else 0
            else:
                past_due_days = None
            report.append({
                "book_id": book.id,
                "title": book.title,
                "rental_status": book.rental_status.value if hasattr(book.rental_status, 'value') else book.rental_status,
                "rentee": user.username if user else None,
                "rented_on": rented_on.strftime('%Y-%m-%d'),
                "due_date": due_date.strftime('%Y-%m-%d'),
                "past_due_days": past_due_days
            })
        else:
            report.append({
                "book_id": book.id,
                "title": book.title,
                "rental_status": book.rental_status.value if hasattr(book.rental_status, 'value') else book.rental_status,
                "rentee": None,
                "rented_on": None,
                "due_date": None,
                "past_due_days": None
            })
    return {"report": report}

@router.post("/books/bulk-create")
async def bulk_upload(
    staff_user: LoggedInStaffUser = Depends(get_current_staff_user),
    db: Session = Depends(get_session),
    file: UploadFile = File(...)
):
    if not staff_user.is_staff:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    if file.content_type not in ["text/csv", "application/vnd.ms-excel"]:
        raise HTTPException(status_code=400, detail="File must be a CSV")
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024: # Max !0 MB
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")
    decoded = contents.decode("utf-8")
    reader = csv.DictReader(decoded.splitlines())
    created = 0
    for row in reader:
        try:
            book_data = BookCreate(
                isbn=row["ISBN"],
                authors=row["Authors"],
                publication_year=int(row["Publication Year"]),
                title=row["Title"],
                language=row["Language"],
                rental_status="available"
            )
            book = BookModel(
                isbn=book_data.isbn,
                authors=book_data.authors,
                publication_year=book_data.publication_year,
                title=book_data.title,
                language=book_data.language,
                rental_status=book_data.rental_status
            )
            db.add(book)
            created += 1
        except Exception as e:
            continue  # skip invalid rows
    db.commit()
    return {"message": f"Bulk upload completed successfully. {created} books added."}



@router.post("/rental")
def rent_book(
    data: RentalRequest,
    background_tasks: BackgroundTasks,
    staff_user: LoggedInStaffUser = Depends(get_current_staff_user),
    db: Session = Depends(get_session),
    
):
    if not staff_user.is_staff:
        raise HTTPException(status_code=403, detail="Not authorized: staff only")
    user_id = data.user
    book_id = data.books
    if not user_id or not book_id:
        raise HTTPException(status_code=400, detail="Missing user or book id")
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    book = db.query(BookModel).filter(BookModel.id == book_id).first()
    if not user or not book:
        raise HTTPException(status_code=404, detail="User or Book not found")
    rental = RentalModel(user_id=user_id, book_id=book_id)
    db.add(rental)
    book.rental_status = RentalStatusEnum.borrowed
    db.commit()
    db.refresh(rental)
    # Email details
    rental_date = rental.rental_date
    due_days = int(os.environ.get("BOOK_RENTAL_DUE_DAYS", 30))
    due_date = rental_date + timedelta(days=due_days)
    subject = f"Book Rental Confirmation: {book.title}"
    body = (
        f"Dear {user.username},\n\n"
        f"You have rented the book '{book.title}' (ID: {book.id}) on {rental_date.strftime('%Y-%m-%d')}.\n"
        f"Your due date is {due_date.strftime('%Y-%m-%d')}.\n\nHappy reading!"
    )
    background_tasks.add_task(send_email, subject=subject, body=body, to=str(user.email))
    return {"message": "Book rented successfully", "rental_id": rental.id}






# @router.get("/books/update-amazon-ids")
# async def update_amazon_ids():
#     """
#     Update Amazon IDs for books.
#     """
#     # Placeholder for actual implementation
#     return {"message": "Amazon IDs updated successfully"}