from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models import (
    ActorModel,
    CountryModel,
    GenreModel,
    LanguageModel,
    MovieModel,
)
from database.session_sqlite import get_sqlite_db
from schemas.movies import (
    MovieCreateSchema,
    MovieDetailResponseSchema,
    MovieListResponseSchema,
    MovieUpdateSchema,
)

movie_router = APIRouter()


@movie_router.get("/", response_model=MovieListResponseSchema)
async def get_movies(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_sqlite_db),
):
    total_result = await db.execute(
        select(func.count()).select_from(MovieModel)
    )
    total_items = total_result.scalar_one()
    total_pages = (
        (total_items + size - 1) // size if total_items > 0 else 1
    )
    offset = (page - 1) * size
    result = await db.execute(
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .offset(offset)
        .limit(size)
    )
    movies = result.scalars().unique().all()
    return MovieListResponseSchema(
        movies=movies,
        total_items=total_items,
        total_pages=total_pages,
        page=page,
        size=size,
        prev_page=f"?page={page - 1}&size={size}" if page > 1 else None,
        next_page=f"?page={page + 1}&size={size}"
        if page < total_pages
        else None,
    )


@movie_router.get("/{movie_id}", response_model=MovieDetailResponseSchema)
async def get_movie(
    movie_id: int, db: AsyncSession = Depends(get_sqlite_db)
):
    result = await db.execute(
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )
    movie = result.scalars().first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie


@movie_router.post(
    "/",
    response_model=MovieDetailResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_movie(
    movie_in: MovieCreateSchema, db: AsyncSession = Depends(get_sqlite_db)
):
    country_res = await db.execute(
        select(CountryModel).where(CountryModel.code == movie_in.country)
    )
    country = country_res.scalars().first()
    if not country:
        country = CountryModel(
            code=movie_in.country, name=movie_in.country
        )
        db.add(country)
        await db.flush()

    genres = []
    for g_name in movie_in.genres:
        g_res = await db.execute(
            select(GenreModel).where(GenreModel.name == g_name)
        )
        genre = g_res.scalars().first()
        if not genre:
            genre = GenreModel(name=g_name)
            db.add(genre)
            await db.flush()
        genres.append(genre)

    actors = []
    for a_name in movie_in.actors:
        a_res = await db.execute(
            select(ActorModel).where(ActorModel.name == a_name)
        )
        actor = a_res.scalars().first()
        if not actor:
            actor = ActorModel(name=a_name)
            db.add(actor)
            await db.flush()
        actors.append(actor)

    languages = []
    for l_name in movie_in.languages:
        l_res = await db.execute(
            select(LanguageModel).where(LanguageModel.name == l_name)
        )
        lang = l_res.scalars().first()
        if not lang:
            lang = LanguageModel(name=l_name)
            db.add(lang)
            await db.flush()
        languages.append(lang)

    movie = MovieModel(
        name=movie_in.name,
        date=movie_in.date,
        score=movie_in.score,
        overview=movie_in.overview,
        status=movie_in.status,
        budget=movie_in.budget,
        revenue=movie_in.revenue,
        country_id=country.id,
        genres=genres,
        actors=actors,
        languages=languages,
    )
    db.add(movie)
    await db.commit()
    await db.refresh(movie)

    res = await db.execute(
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == movie.id)
    )
    return res.scalars().first()


@movie_router.put(
    "/{movie_id}", response_model=MovieDetailResponseSchema
)
async def update_movie(
    movie_id: int,
    movie_in: MovieUpdateSchema,
    db: AsyncSession = Depends(get_sqlite_db),
):
    res = await db.execute(
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )
    movie = res.scalars().first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    country_res = await db.execute(
        select(CountryModel).where(CountryModel.code == movie_in.country)
    )
    country = country_res.scalars().first()
    if not country:
        country = CountryModel(
            code=movie_in.country, name=movie_in.country
        )
        db.add(country)
        await db.flush()

    genres = []
    for g_name in movie_in.genres:
        g_res = await db.execute(
            select(GenreModel).where(GenreModel.name == g_name)
        )
        genre = g_res.scalars().first()
        if not genre:
            genre = GenreModel(name=g_name)
            db.add(genre)
            await db.flush()
        genres.append(genre)

    actors = []
    for a_name in movie_in.actors:
        a_res = await db.execute(
            select(ActorModel).where(ActorModel.name == a_name)
        )
        actor = a_res.scalars().first()
        if not actor:
            actor = ActorModel(name=a_name)
            db.add(actor)
            await db.flush()
        actors.append(actor)

    languages = []
    for l_name in movie_in.languages:
        l_res = await db.execute(
            select(LanguageModel).where(LanguageModel.name == l_name)
        )
        lang = l_res.scalars().first()
        if not lang:
            lang = LanguageModel(name=l_name)
            db.add(lang)
            await db.flush()
        languages.append(lang)

    movie.name = movie_in.name
    movie.date = movie_in.date
    movie.score = movie_in.score
    movie.overview = movie_in.overview
    movie.status = movie_in.status
    movie.budget = movie_in.budget
    movie.revenue = movie_in.revenue
    movie.country_id = country.id
    movie.genres = genres
    movie.actors = actors
    movie.languages = languages

    await db.commit()
    await db.refresh(movie)
    return movie


@movie_router.delete(
    "/{movie_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_movie(
    movie_id: int, db: AsyncSession = Depends(get_sqlite_db)
):
    res = await db.execute(
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )
    movie = res.scalars().first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    await db.delete(movie)
    await db.commit()
    return None
