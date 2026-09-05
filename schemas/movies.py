from pydantic import BaseModel, Field, ConfigDict
from datetime import date
from typing import List, Optional


class Entity(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class Country(BaseModel):
    id: int
    code: str
    name: Optional[str]
    model_config = ConfigDict(from_attributes=True)


class MovieCreateSchema(BaseModel):
    name: str = Field(..., max_length=255)
    date: date
    score: float = Field(..., ge=0.0, le=100.0)
    overview: str
    status: str = Field(..., pattern="^(Released|Post Production|In Production)$")
    budget: float = Field(..., ge=0.0)
    revenue: float = Field(..., ge=0.0)
    country: str = Field(..., min_length=3, max_length=3)
    genres: List[str]
    actors: List[str]
    languages: List[str]


class MovieUpdateSchema(MovieCreateSchema):
    pass


class MovieDetailResponseSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: Country
    genres: List[Entity]
    actors: List[Entity]
    languages: List[Entity]
    model_config = ConfigDict(from_attributes=True)


class MovieListResponseSchema(BaseModel):
    movies: List[MovieDetailResponseSchema]
    total_items: int
    total_pages: int
    page: int
    size: int
    prev_page: Optional[str]
    next_page: Optional[str]
