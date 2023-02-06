from __future__ import annotations
from typing import Any, Generic, Mapping, Sequence, TypeVar, TYPE_CHECKING

from bson import ObjectId
from pydantic import BaseModel
from pymongo.collation import Collation
from pymongo.results import DeleteResult, InsertOneResult, UpdateResult

if TYPE_CHECKING:
    from motor.motor_asyncio import (
        AsyncIOMotorCollection,
        AsyncIOMotorCursor,
        AsyncIOMotorDatabase,
        AsyncIOMotorLatentCommandCursor,
    )

    from .typing import (
        AsyncIOMotorClientSession,
        CollectionOptions,
        DeleteOptions,
        FindOptions,
        InsertOneOptions,
        MongoProjection,
        MongoQuery,
        UpdateManyOptions,
        UpdateObject,
        UpdateOneOptions,
    )

TInsert = TypeVar("TInsert", bound=BaseModel)
TUpdate = TypeVar("TUpdate", bound=BaseModel)


class MongoService(Generic[TInsert, TUpdate]):
    """
    Base service with typed utility methods for MongoDB (`motor` asyncio).

    The service provides a limited subset of `motor`'s capabilities.

    For undocumented keyword arguments, please see the `motor` or `pymongo` documentation.
    """

    __slots__ = (
        "_collection",
        "_collection_name",
        "_collection_options",
        "_database",
    )

    def __init__(
        self,
        database: AsyncIOMotorDatabase,
        collection_name: str,
        collection_options: CollectionOptions | None = None,
    ) -> None:
        """
        Initialization.

        Arguments:
            database: The database driver.
            collection_name: The name of the collection the service works with.
            collection_options: Collection configuration options.
        """
        self._database = database
        self._collection_name = collection_name
        self._collection_options = collection_options
        self._collection: AsyncIOMotorCollection | None = None

    @property
    def collection(self) -> AsyncIOMotorCollection:
        """
        The collection instance of the service.
        """
        if self._collection is None:
            self._collection = self._create_collection()

        return self._collection

    @property
    def collection_name(self) -> str:
        """
        The name of the collection the service works with.
        """
        return self._collection_name

    def aggregate(
        self,
        pipeline: Sequence[dict[str, Any]],
        session: AsyncIOMotorClientSession | None = None,
        **kwargs: Any,
    ) -> AsyncIOMotorLatentCommandCursor:
        """
        Performs an aggregation.

        For undocumented keyword arguments, see the documentation of `pymongo.collection.Collection.aggregate()`.

        Arguments:
            pipeline: The aggregation pipeline.
            session: An optional session to use.
        """
        return self.collection.aggregate(pipeline, session=session, **kwargs)

    async def create_index(
        self,
        keys: str | Sequence[tuple[str, int | str | Mapping[str, Any]]],
        *,
        name: str,
        unique: bool = False,
        session: AsyncIOMotorClientSession | None = None,
        background: bool = False,
        collation: Collation | None = None,
        sparse: bool = False,
        **kwargs: Any,
    ) -> str:
        """
        Creates the specified index on collection of the service.

        Arguments:
            keys: Index description.
            name: Index name.
            unique: Whether to create a uniqueness constraint on the index.
            session: An optional session to use.
            background: Whether the index should be created in the background.
            collation: A `Collation` instance.
            sparse: Whether to omit documents from the index that doesn't have the indexed field.
        """
        return await self.collection.create_index(
            keys,
            name=name,
            unique=unique,
            session=session,
            background=background,
            collation=collation,
            sparse=sparse,
            **kwargs,
        )

    async def drop_index(
        self,
        index_or_name: str | Sequence[tuple[str, int | str | Mapping[str, Any]]],
        session: AsyncIOMotorClientSession | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Drops the given index from the collection of the service.

        Arguments:
            index_or_name: The index to drop.
            session: An optional session to use.
        """
        return await self.collection.drop_index(index_or_name, session=session, **kwargs)

    async def drop_indexes(self, session: AsyncIOMotorClientSession | None = None, **kwargs: Any) -> None:
        """
        Drops all indexes from the collection of the service.

        Arguments:
            session: An optional session to use.
        """
        return await self.collection.drop_index(session, **kwargs)

    def list_indexes(
        self,
        session: AsyncIOMotorClientSession | None = None,
        **kwargs: Any,
    ) -> AsyncIOMotorLatentCommandCursor:
        """
        Returns a cursor over the indexes of the collection of the service.

        Arguments:
            session: An optional session to use.
        """
        return self.collection.list_indexes(session, **kwargs)

    async def delete_by_id(
        self,
        id: ObjectId,
        *,
        options: DeleteOptions | None = None,
    ) -> DeleteResult:
        """
        Deletes the document with the given ID.

        This method is just a wrapper around `delete_one()`.

        Arguments:
            id: The ID of the document to delete.
            options: Delete options, see the arguments of `collection.delete_one()`.

        Returns:
            The result of the operation.
        """
        return await self.delete_one({"_id": id}, options=options)

    async def delete_many(
        self,
        query: MongoQuery | None,
        *,
        options: DeleteOptions | None = None,
    ) -> DeleteResult:
        """
        The default `delete_many()` implementation of the service.

        Arguments:
            query: Query object that matches the documents that should be deleted.
            options: Delete options, see the arguments of `collection.delete_many()`.

        Returns:
            The result of the operation.
        """
        return await self.collection.delete_many(query, **(options or {}))

    async def delete_one(
        self,
        query: MongoQuery | None,
        *,
        options: DeleteOptions | None = None,
    ) -> DeleteResult:
        """
        The default `delete_one()` implementation of the service.

        Arguments:
            query: Query object that matches the document that should be deleted.
            options: Delete options, see the arguments of `collection.delete_one()`.

        Returns:
            The result of the operation.
        """
        return await self.collection.delete_one(query, **(options or {}))

    def find(
        self,
        query: MongoQuery | None = None,
        projection: MongoProjection | None = None,
        *,
        options: FindOptions | None = None,
    ) -> AsyncIOMotorCursor:
        """
        The default `find()` implementation of the service.

        Arguments:
            query: The query object.
            projection: Optional projection.
            options: Query options, see the arguments of `collection.find()` for details.

        Returns:
            An async database cursor.
        """
        return self.collection.find(query, projection, **(options or {}))

    async def find_one(
        self,
        query: MongoQuery | None = None,
        projection: MongoProjection | None = None,
        *,
        options: FindOptions | None = None,
    ) -> dict[str, Any] | None:
        """
        The default `find_one()` implementation of the service.

        Arguments:
            query: The query object.
            projection: Optional projection.
            options: Query options, see the arguments of `collection.find()` for details.

        Returns:
            A single matching document or `None` if there are no matches.
        """
        return await self.collection.find_one(query, projection, **(options or {}))

    async def get_by_id(
        self,
        id: ObjectId,
        projection: MongoProjection | None = None,
        *,
        options: FindOptions | None = None,
    ) -> dict[str, Any] | None:
        """
        Returns the document with the given ID if it exists.

        Arguments:
            id: The ID of the queried document. Must be an `ObjectID`, not a `str`.
            projection: Optional projection.
            options: Query options, see the arguments of `collection.find()` for details.

        Returns:
            The queried document if such a document exists.
        """
        return await self.find_one({"_id": id}, projection, options=options)

    async def insert_one(self, data: TInsert, *, options: InsertOneOptions | None = None) -> InsertOneResult:
        """
        Inserts the given data into the collection.

        Arguments:
            data: The data to be inserted.
            options: Insert options, see the arguments of `collection.insert_one()` for details.

        Returns:
            The result of the operation.

        Raises:
            Exception: if the data is invalid.
        """
        return await self.collection.insert_one(self._prepare_for_insert(data), **(options or {}))

    async def update_by_id(
        self,
        id: ObjectId,
        changes: TUpdate,
        *,
        options: UpdateOneOptions | None = None,
    ) -> UpdateResult:
        """
        Updates the document with the given ID.

        Arguments:
            id: The ID of the document to update.
            changes: The changes to make.
            options: Update options, see the arguments of `collection.update_one()` for details.

        Returns:
            The result of the operation.
        """
        return await self.update_one({"_id": id}, changes, options=options)

    async def update_many(
        self,
        query: MongoQuery | None,
        changes: TUpdate,
        *,
        options: UpdateManyOptions | None = None,
    ) -> UpdateResult:
        """
        The default `delete_many()` implementation of the service.

        Arguments:
            query: Query that matches the documents that should be updated.
            changes: The changes to make.
            options: Update options, see the arguments of `collection.update_many()` for details.

        Returns:
            The result of the operation.
        """
        return await self.collection.update_many(query, self._prepare_for_update(changes), **(options or {}))

    async def update_one(
        self,
        query: MongoQuery | None,
        changes: TUpdate,
        *,
        options: UpdateOneOptions | None = None,
    ) -> UpdateResult:
        """
        The default `delete_one()` implementation of the service.

        Arguments:
            query: Query that matches the document that should be updated.
            changes: The changes to make.
            options: Update options, see the arguments of `collection.update_one()` for details.

        Returns:
            The result of the operation.
        """
        return await self.collection.update_one(query, self._prepare_for_update(changes), **(options or {}))

    def _create_collection(self) -> AsyncIOMotorCollection:
        """
        Creates a new `AsyncIOMotorCollection` instance for the service.
        """
        return self._database.get_collection(self._collection_name, **(self._collection_options or {}))

    def _prepare_for_insert(self, data: TInsert) -> dict[str, Any]:
        """
        Hook that is called before inserting the given data into the collection.

        The default implementation is simply `data.dict()`.

        Arguments:
            data: The data to be inserted.

        Returns:
            The MongoDB-compatible, insertable data.

        Raises:
            Exception: if the data is invalid.
        """
        return data.dict()

    def _prepare_for_update(self, data: TUpdate) -> UpdateObject | Sequence[UpdateObject]:
        """
        Hook that is called before applying the given update.

        The default implementation is `{"$set": data.dict(exclude_unset=True)}`.

        Arguments:
            data: The update data.

        Returns:
            The MongoDB-compatible update object.

        Raises:
            Exception: if the data is invalid.
        """
        return {"$set": data.dict(exclude_unset=True)}
