from fastapi import APIRouter
from routes.movies import router as movie_router

api_router = APIRouter()
api_router.include_router(movie_router, prefix="/movies", tags=["movies"])
