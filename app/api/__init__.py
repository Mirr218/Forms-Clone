from .auth import router as auth_router
from .forms import router as forms_router
from .submissions import router as submissions_router

__all__ = ["auth_router", "forms_router", "submissions_router"]
