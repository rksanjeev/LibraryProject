from fastapi import APIRouter
from .auth import router as auth_router
from .users import router as users_router
from .admin import router as rentals_router

v1_router = APIRouter(prefix="/api/v1")

v1_router.include_router(
    auth_router,
    tags=["auth"],
)
v1_router.include_router(
    users_router,
    tags=["users"],
)
v1_router.include_router(
    rentals_router,
    tags=["admin"],
)


@v1_router.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint to verify the API is running.
    """
    return {"status": "ok", "message": "API is running"}
