from fastapi import APIRouter

from .auth import router as auth_router
from .forms import router as forms_router
from .submissions import router as submissions_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(forms_router)
api_router.include_router(submissions_router)

__all__ = ["api_router", "auth_router", "forms_router", "submissions_router"]
