import os
from fastapi import APIRouter
from fastapi import UploadFile, File
from db import get_session
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException
from services.auth import confirm_staff_token, get_current_staff_user
from schema.users import LoggedInStaffUser


router = APIRouter(prefix="/admin", tags=["admin"])

BOOK_RENTAL_DUE_DAYS = os.environ.get("BOOK_RENTAL_DUE_DAYS", 30) # Default rental period in days

@router.get("/confirm-staff-access")
def confirm_staff_access(token: str, db: Session = Depends(get_session)):
    try:
        user = confirm_staff_token(token, db)
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    return {"msg": "Email confirmed. You can now log in."}

@router.post("/rental")
async def manage_rentals(staff_user: LoggedInStaffUser = Depends(get_current_staff_user), db :Session = Depends(get_session)):
    """
    Manage rentals for an admin.
    """
    # Placeholder for actual implementation
    return {"message": "Rentals managed successfully"}

@router.post("/rental/return")
async def return_rental(staff_user: LoggedInStaffUser = Depends(get_current_staff_user), db :Session = Depends(get_session)):
    """
    Return a rental item.
    """
    # Placeholder for actual implementation
    return {"message": "Rental item returned successfully"}

@router.post("/rental/extend")
async def extend_rental(staff_user: LoggedInStaffUser = Depends(get_current_staff_user), db :Session = Depends(get_session)):
    """
    Extend a rental item.
    """
    # Placeholder for actual implementation
    return {"message": "Rental item extended successfully"}

@router.get("/rental/report")
async def rental_report(staff_user: LoggedInStaffUser = Depends(get_current_staff_user), db :Session = Depends(get_session),username: int | None = None):
    """
    Generate a rental report for an admin.
    """
    # Placeholder for actual implementation
    if username:
        return {"message": f"Rental report for user {username}"}
    return {"message": "Rental report generated successfully"}


@router.post("/books/bulk-create")
async def bulk_upload(staff_user: LoggedInStaffUser = Depends(get_current_staff_user), db :Session = Depends(get_session), file: UploadFile = File(...)):
    """
    Bulk upload items for an admin.
    """
    
    # Placeholder for actual implementation
    return {"message": "Bulk upload completed successfully"}


@router.get("/books/update-amazon-ids")
async def update_amazon_ids():
    """
    Update Amazon IDs for books.
    """
    # Placeholder for actual implementation
    return {"message": "Amazon IDs updated successfully"}