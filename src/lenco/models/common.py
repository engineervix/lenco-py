"""Shared envelope pieces used across resources."""

from dataclasses import dataclass
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

T = TypeVar("T")


class LencoModel(BaseModel):
    """Base model: Python snake_case fields, Lenco camelCase JSON keys."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class Meta(LencoModel):
    """Pagination context returned in the ``meta`` key of list responses."""

    total: int
    page_count: int
    per_page: int
    current_page: int


@dataclass
class Paginated(Generic[T]):
    """A page of results plus its pagination metadata."""

    items: list[T]
    meta: Meta | None
