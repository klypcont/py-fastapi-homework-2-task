from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from datetime import date, timedelta
from typing import List

from database.db import get_db
from models.movies import Movie as MovieModel, Country, Genre, Actor, Language
from schemas.movies import (
    MovieListResponseSchema,
    MovieDetailResponseSchema,
    MovieCreateSchema,
    MovieUpdateSchema,
)

router = APIRouter(prefix="/theater/movies", tags=["movies"])


async def get_or_create(db: AsyncSession, model, names: List[str]):
    objs = []
    for name in names:
        stmt = select(model).where(model.name == name)
        result = await db.execute(stmt)
        obj = result.scalars().first()
        if not obj:
            obj = model(name=name)
            db.add(obj)
        objs.append(obj)
    return objs


@router.get("/", response_model=MovieListResponseSchema)
async def get_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * per_page

    count_stmt = select(func.count()).select_from(MovieModel)
    total_items = (await db.scalar(count_stmt)) or 0
    total_pages = (total_items + per_page - 1) // per_page if total_items > 0 else 1

    stmt = (
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .order_by(MovieModel.id.desc())
        .offset(offset)
        .limit(per_page)
    )
    result = await db.execute(stmt)
    movies = result.scalars().unique().all()

    base_path = "/theater/movies/"
    prev_page = f"{base_path}?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"{base_path}?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return {
        "movies": movies,
        "total_items": total_items,
        "total_pages": total_pages,
        "page": page,
        "size": per_page,
        "prev_page": prev_page,
        "next_page": next_page,
    }


@router.get("/{movie_id}/", response_model=MovieDetailResponseSchema)
async def get_movie_by_id(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )
    result = await db.execute(stmt)
    movie = result.scalars().unique().one_or_none()

    if not movie:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found")

    return movie


@router.post("/", response_model=MovieDetailResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_movie(
    movie_data: MovieCreateSchema,
    db: AsyncSession = Depends(get_db)
):
    if movie_data.date > date.today() + timedelta(days=365):
        raise HTTPException(status_code=400, detail="Release date cannot be more than 1 year in the future.")

    stmt = select(MovieModel).where(MovieModel.name == movie_data.name, MovieModel.date == movie_data.date)
    result = await db.execute(stmt)
    if result.scalars().first():
        raise HTTPException(status_code=409, detail="Movie with this name and date already exists.")

    country_stmt = select(Country).where(Country.code == movie_data.country)
    country_result = await db.execute(country_stmt)
    country_obj = country_result.scalars().first()
    if not country_obj:
        country_obj = Country(code=movie_data.country, name="Unknown")
        db.add(country_obj)
        await db.flush()

    new_movie = MovieModel(
        name=movie_data.name,
        date=movie_data.date,
        score=movie_data.score,
        overview=movie_data.overview,
        status=movie_data.status,
        budget=movie_data.budget,
        revenue=movie_data.revenue,
        country_id=country_obj.id
    )

    new_movie.genres = await get_or_create(db, Genre, movie_data.genres)
    new_movie.actors = await get_or_create(db, Actor, movie_data.actors)
    new_movie.languages = await get_or_create(db, Language, movie_data.languages)

    db.add(new_movie)
    await db.commit()
    await db.refresh(new_movie)

    stmt_reload = (
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == new_movie.id)
    )
    reload_result = await db.execute(stmt_reload)
    return reload_result.scalars().unique().one()


@router.put("/{movie_id}/", response_model=MovieDetailResponseSchema)
async def update_movie(
    movie_id: int,
    movie_data: MovieUpdateSchema,
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )
    result = await db.execute(stmt)
    movie = result.scalars().unique().one_or_none()

    if not movie:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found")

    if movie_data.date > date.today() + timedelta(days=365):
        raise HTTPException(status_code=400, detail="Release date cannot be more than 1 year in the future.")

    dup_stmt = select(MovieModel).where(
        MovieModel.name == movie_data.name,
        MovieModel.date == movie_data.date,
        MovieModel.id != movie_id
    )
    dup_result = await db.execute(dup_stmt)
    if dup_result.scalars().first():
        raise HTTPException(status_code=409, detail="Movie with this name and date already exists.")

    country_stmt = select(Country).where(Country.code == movie_data.country)
    country_result = await db.execute(country_stmt)
    country_obj = country_result.scalars().first()
    if not country_obj:
        country_obj = Country(code=movie_data.country, name="Unknown")
        db.add(country_obj)
        await db.flush()

    movie.name = movie_data.name
    movie.date = movie_data.date
    movie.score = movie_data.score
    movie.overview = movie_data.overview
    movie.status = movie_data.status
    movie.budget = movie_data.budget
    movie.revenue = movie_data.revenue
    movie.country_id = country_obj.id

    movie.genres = await get_or_create(db, Genre, movie_data.genres)
    movie.actors = await get_or_create(db, Actor, movie_data.actors)
    movie.languages = await get_or_create(db, Language, movie_data.languages)

    await db.commit()
    await db.refresh(movie)
    return movie


@router.delete("/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found")

    await db.delete(movie)
    await db.commit()
    return
