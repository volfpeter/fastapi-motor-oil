from __future__ import annotations
from typing import Any, Mapping, Sequence, TypedDict, TYPE_CHECKING

from motor.motor_asyncio import AsyncIOMotorClientSession  # Reexported

if TYPE_CHECKING:
    from bson.codec_options import CodecOptions
    from pymongo.collation import Collation
    from pymongo.read_concern import ReadConcern
    from pymongo.read_preferences import Primary, PrimaryPreferred, Secondary, SecondaryPreferred, Nearest
    from pymongo.write_concern import WriteConcern


MongoProjection = dict[str, Any]


MongoQuery = dict[str, Any]


UpdateObject = dict[str, Any] | Sequence[dict[str, Any]]


class CollectionOptions(TypedDict, total=False):
    codec_options: CodecOptions | None  # Default is None
    read_preference: Primary | PrimaryPreferred | Secondary | SecondaryPreferred | Nearest | None  # Default  None
    write_concern: WriteConcern | None  # Default is None
    read_concern: ReadConcern | None  # Default is None


class DeleteOptions(TypedDict, total=False):
    collation: Mapping[str, Any] | Collation | None  # Default is None
    hint: str | Sequence[tuple[str, int | str | Mapping[str, Any]]] | None  # Default is None
    session: AsyncIOMotorClientSession | None  # Default is None
    let: Mapping[str, Any] | None  # Default is None
    comment: Any | None  # Default is None


class FindOptions(TypedDict, total=False):
    skip: int  # Default is 0
    limit: int  # Default is 0
    no_cursor_timeout: bool  # Default is False
    cursor_type: int  # Default is pymongo.cursor.CursorType.NON_TAILABLE
    sort: Sequence[tuple[str, int | str | Mapping[str, Any]]] | None  # Default is None
    allow_partial_results: bool  # Default is False
    oplog_replay: bool  # Default is False
    batch_size: int  # Default is 0
    collation: Mapping[str, Any] | Collation | None  # Default is None
    hint: str | Sequence[tuple[str, int | str | Mapping[str, Any]]] | None  # Default is None
    max_scan: int | None  # Default is None
    max_time_ms: int | None  # Default is None
    max: Sequence[tuple[str, int | str | Mapping[str, Any]]] | None  # Default is None
    min: Sequence[tuple[str, int | str | Mapping[str, Any]]] | None  # Default is None
    return_key: bool | None  # Default is None
    show_record_id: bool | None  # Default is None
    snapshot: bool | None  # Default is None
    comment: Any | None  # Default is None
    session: AsyncIOMotorClientSession | None  # Default is None
    allow_disk_use: bool | None  # Default is None
    let: bool | None  # Default is None


class InsertOneOptions(TypedDict, total=False):
    bypass_document_validation: bool  # Default is False
    session: AsyncIOMotorClientSession | None  # Default is None
    comment: Any | None  # Default is None


class UpdateOneOptions(TypedDict, total=False):
    upsert: bool  # Default is False
    bypass_document_validation: bool  # Default is False
    collation: Mapping[str, Any] | Collation | None  # Default is None
    array_filters: Sequence[Mapping[str, Any]]  # Default is None
    hint: str | Sequence[tuple[str, int | str | Mapping[str, Any]]] | None  # Default is None
    session: AsyncIOMotorClientSession | None  # Default is None
    let: Mapping[str, Any] | None  # Default is None
    comment: Any | None  # Default is None


class UpdateManyOptions(TypedDict, total=False):
    upsert: bool  # Default is False
    array_filters: Sequence[Mapping[str, Any]] | None  # Default is None
    bypass_document_validation: bool  # Default is None
    collation: Mapping[str, Any] | Collation | None  # Default is None
    hint: str | Sequence[tuple[str, int | str | Mapping[str, Any]]] | None  # Default is None
    session: AsyncIOMotorClientSession | None  # Default is None
    let: Mapping[str, Any] | None  # Default is None
    comment: Any | None  # Default is None
