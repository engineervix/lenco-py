"""Shared helpers for resource classes."""

from typing import Any, TypeVar

from pydantic import BaseModel

from .._http import Envelope
from ..models import Meta, Paginated

T = TypeVar("T", bound=BaseModel)


def paginated(envelope: Envelope, model: type[T]) -> Paginated[T]:
    """Build a :class:`Paginated` from a list-response envelope."""
    items: list[Any] = envelope.data or []
    return Paginated(
        items=[model.model_validate(i) for i in items],
        meta=Meta.model_validate(envelope.meta) if envelope.meta else None,
    )


def one(envelope: Envelope, model: type[T]) -> T:
    """Validate the ``data`` key of a single-object response envelope."""
    return model.model_validate(envelope.data)


def drop_nones(payload: dict[str, Any]) -> dict[str, Any]:
    """Remove keys whose value is ``None`` from a request body."""
    return {k: v for k, v in payload.items() if v is not None}
