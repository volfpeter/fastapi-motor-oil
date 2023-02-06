from __future__ import annotations
from typing import Any, Callable, Generator, Protocol

from datetime import datetime, timezone

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pydantic import BaseModel, Field
from pydantic.datetime_parse import parse_datetime


class ClientProvider(Protocol):
    """
    Client provider protocol for FastAPI database dependencies.
    """

    def __call__(self) -> AsyncIOMotorClient:
        ...


class DatabaseProvider(Protocol):
    """
    Database provider protocol for FastAPI database dependencies.
    """

    def __call__(self) -> AsyncIOMotorDatabase:
        ...


class UTCDatetime(datetime):
    @classmethod
    def __get_validators__(cls):
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
    Custom BSON ObjectID for use with Pydantic.
    """

    @classmethod
    def __get_validators__(cls) -> Generator[Callable, None, None]:
        yield cls.validate

    @classmethod
    def validate(cls, value: Any) -> StrObjectId:
        if not ObjectId.is_valid(value):
            raise ValueError("Invalid StrObjectID")
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
