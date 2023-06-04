from __future__ import annotations

from collections.abc import Callable, Generator
from datetime import datetime, timezone
from typing import Any, Protocol

from bson import ObjectId
from motor.core import AgnosticClient, AgnosticDatabase
from pydantic import BaseModel, Field
from pydantic.datetime_parse import parse_datetime

__all__ = (
    "AgnosticClient",
    "AgnosticDatabase",
    "ClientProvider",
    "DatabaseProvider",
    "UTCDatetime",
    "StrObjectId",
    "DocumentModel",
    "DeleteResultModel",
)


class ClientProvider(Protocol):
    """
    Client provider protocol for FastAPI database dependencies.
    """

    def __call__(self) -> AgnosticClient:
        ...


class DatabaseProvider(Protocol):
    """
    Database provider protocol for FastAPI database dependencies.
    """

    def __call__(self) -> AgnosticDatabase:
        ...


class UTCDatetime(datetime):
    """
    Pydantic datetime field that enforces UTC timezone.
    """

    @classmethod
    def __get_validators__(cls) -> Generator[Any, None, None]:
        yield parse_datetime  # default pydantic behavior
        yield cls.ensure_utc

    @classmethod
    def ensure_utc(cls, value: datetime) -> datetime:
        """
        Makes sure the given datetime is in UTC.

        If `value` has no timezone info, the method sets UTC.

        Raises:
            ValueError: If `value` has timezone info but it's not UTC.
        """
        tzinfo = value.tzinfo
        if tzinfo is None:  # No timezone info, assume UTC.
            return value.replace(tzinfo=timezone.utc)

        if tzinfo == timezone.utc:  # Timezone is UTC, no-op.
            return value

        # Non-UTC timezone info, raise exception.
        raise ValueError("Non-UTC timezone.")


class StrObjectId(ObjectId):
    """
    Custom BSON `ObjectId` for use with Pydantic.
    """

    @classmethod
    def __get_validators__(cls) -> Generator[Callable[[Any], StrObjectId], None, None]:
        yield cls.validate

    @classmethod
    def validate(cls, value: Any) -> StrObjectId:
        """
        Checks whether the given value is a valid `ObjectId`"""
        if not ObjectId.is_valid(value):
            raise ValueError("Invalid StrObjectId")
        return cls(value)

    @classmethod
    def __modify_schema__(cls, field_schema: dict[str, Any]) -> None:
        field_schema.update(type="string")


class DocumentModel(BaseModel):
    """
    Pydantic base model for MongoDB documents.

    It exposes the `_id` attribute as `id`.
    """

    id: StrObjectId = Field(alias="_id")

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class DeleteResultModel(BaseModel):
    """
    Delete result model.
    """

    delete_count: int
