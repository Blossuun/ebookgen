"""API route modules for ebookgen."""

from api.routes.books import router as books_router
from api.routes.jobs import router as jobs_router
from api.routes.output import router as output_router
from api.routes.ws import router as ws_router

__all__ = ["books_router", "jobs_router", "output_router", "ws_router"]
