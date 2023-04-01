# FastAPI example

In this is example we will:

- create a simple `TreeNode` document model with a name, a creation date, and an optional reference to a parent node;
- prepare all the services that are necessary to create, read, update, or delete documents;
- declare a couple of delete rules and validators that enforce consistency;
- declare a unique name index for the `TreeNode` collection;
- implement a `fastapi` `APIRouter` factory that can be included in `fastapi` applications;
- set up the `fastapi` application itself;
- implement automatic index creation in the application's lifespan method.

## Prerequisites

To follow and try this example, you will need:

- Python 3.10+;
- access to a MongoDB database (e.g. a Community Edition running locally);
- `fastapi` with all its dependencies (`pip install fastapi[all]`);
- and of course this library.

## Project layout

Create the _root directory_ of your project, for example `tree-app`.

Inside the _root directory_, create the root Python _package_ for the application -- `tree_app` -- and add the following empty files to:

- `__init__.py`
- `api.py`
- `main.py`
- `model.py`
- `service.py`

In the end, your directory structure should look like this:

<ul>
    <li><code>tree-app</code> (root directory)</li>
    <ul>
        <li><code>tree_app</code> (root package)</li>
        <ul>
            <li><code>__init__.py</code></li>
            <li><code>api.py</code></li>
            <li><code>main.py</code></li>
            <li><code>model.py</code></li>
            <li><code>service.py</code></li>
        </ul>
    </ul>
</ul>

## Model

First we will implement the data model in `model.py`. Actually, we will implement three (`pydantic`) model classes, one for document serialization, one for creation, and one for editing.

```python
from fastapi_motor_oil import DocumentModel, StrObjectId, UTCDatetime
from pydantic import BaseModel

class TreeNode(DocumentModel):
    """
    Tree node document model.
    """

    name: str
    parent: StrObjectId | None
    created_at: UTCDatetime

class TreeNodeCreate(BaseModel):
    """
    Tree node creation model.
    """

    name: str
    parent: StrObjectId | None

class TreeNodeUpdate(BaseModel):
    """
    Tree node update model.
    """

    name: str | None
    parent: StrObjectId | None
```

## Services

With the model in place, we can start working on the services (`service.py`) that we will use from the REST routes. This step is as simple as subclassing `MongoService` and specifying the collection name:

```python
from typing import Any
from datetime import datetime, timezone

from fastapi_motor_oil import CollectionOptions, MongoService

from .model import TreeNodeCreate, TreeNodeUpdate

class TreeNodeService(MongoService[TreeNodeCreate, TreeNodeUpdate]):
    """
    Tree node database services.
    """

    __slots__ = ()

    collection_name: str = "tree_nodes"

    collection_options: CollectionOptions | None = None

    async def _convert_for_insert(self, data: TreeNodeCreate) -> dict[str, Any]:
        return {
            **(await super()._convert_for_insert(data)),
            "created_at": datetime.now(timezone.utc),
        }
```

Noticate that `TreeNodeCreate` does not have a `created_at` attribute. Instead we inject this attribute during creation by overriding the `_convert_for_insert()` method of the service.

That could be it, but we want to enforce a level of consistency in the database. To do that, we will add a couple of delete rules and validators to the service.

Note that the rules below do _not_ fully enforce a tree structure, but they are good enough for demonstration purposes.

```python
from typing import Any
from collections.abc import Sequence
from datetime import datetime, timezone

from bson import ObjectId
from fastapi_motor_oil import CollectionOptions, MongoQuery, MongoService, delete_rule, validator
from motor.core import AgnosticClientSession

from .model import TreeNodeCreate, TreeNodeUpdate

class TreeNodeService(MongoService[TreeNodeCreate, TreeNodeUpdate]):
    """
    Tree node database services.
    """

    __slots__ = ()

    collection_name: str = "tree_nodes"

    collection_options: CollectionOptions | None = None

    @delete_rule("pre")  # Delete rule that remove the subtrees of deleted nodes.
    async def dr_delete_subtree(self, session: AgnosticClientSession, ids: Sequence[ObjectId]) -> None:
        child_ids = await self.find_ids({"parent": {"$in": ids}}, session=session)
        if len(child_ids) > 0:
            # Recursion
            await self.delete_many({"_id": {"$in": child_ids}}, options={"session": session})

    @delete_rule("deny")  # Delete rule that prevents the removal of root nodes.
    async def dr_deny_if_root(self, session: AgnosticClientSession, ids: Sequence[ObjectId]) -> None:
        root_cnt = await self.count_documents(
            {"$and": [{"_id": {"$in": ids}}, {"parent": None}]},
            options={"session": session},
        )
        if root_cnt > 0:
            raise ValueError("Can not delete root nodes.")

    @validator("insert-update")
    async def v_parent_valid(self, query: MongoQuery | None, data: TreeNodeCreate | TreeNodeUpdate) -> None:
        if data.parent is None:  # No parent node is always fine
            return

        if not await self.exists(data.parent):  # Parent must exist.
            raise ValueError("Parent does not exist.")

        if isinstance(data, TreeNodeCreate):  # No more checks during creation.
            return

        matched_ids = (await self.find_ids(query)) if isinstance(data, TreeNodeUpdate) else []
        if data.parent in matched_ids:  # Self reference is forbidden.
            raise ValueError("Self-reference.")

    async def _convert_for_insert(self, data: TreeNodeCreate) -> dict[str, Any]:
        return {
            **(await super()._convert_for_insert(data)),
            "created_at": datetime.now(timezone.utc),
        }
```

Finally, we will declare the indexes of the collection by setting `TreeNodeService.indexes`, which must be an index name - `IndexData` dictionary. A unique, ascending, case-insensitive index on the `name` attribute can be declared like this:

```python
...
from fastapi_motor_oil import IndexData, MongoService

...

from .model import TreeNodeCreate, TreeNodeUpdate
...

class TreeNodeService(MongoService[TreeNodeCreate, TreeNodeUpdate]):
    ...

    indexes = {
        "unique-name": IndexData(
            keys="name",
            unique=True,
            collation={"locale": "en", "strength": 1},
        ),
    }

    ...
```

For all indexing options, please see the [PyMongo documentation](https://pymongo.readthedocs.io/en/stable/index.html).

Combining everything together, the final service implementation looks like this:

```python
from typing import Any
from collections.abc import Sequence
from datetime import datetime, timezone

from bson import ObjectId
from fastapi_motor_oil import CollectionOptions, IndexData, MongoQuery, MongoService, delete_rule, validator
from motor.core import AgnosticClientSession

from .model import TreeNodeCreate, TreeNodeUpdate

class TreeNodeService(MongoService[TreeNodeCreate, TreeNodeUpdate]):
    """
    Tree node database services.
    """

    __slots__ = ()

    collection_name: str = "tree_nodes"

    collection_options: CollectionOptions | None = None

    indexes = {
        "unique-name": IndexData(
            keys="name",
            unique=True,
            collation={"locale": "en", "strength": 1},
        ),
    }

    @delete_rule("pre")  # Delete rule that remove the subtrees of deleted nodes.
    async def dr_delete_subtree(self, session: AgnosticClientSession, ids: Sequence[ObjectId]) -> None:
        child_ids = await self.find_ids({"parent": {"$in": ids}}, session=session)
        if len(child_ids) > 0:
            # Recursion
            await self.delete_many({"_id": {"$in": child_ids}}, options={"session": session})

    @delete_rule("deny")  # Delete rule that prevents the removal of root nodes.
    async def dr_deny_if_root(self, session: AgnosticClientSession, ids: Sequence[ObjectId]) -> None:
        root_cnt = await self.count_documents(
            {"$and": [{"_id": {"$in": ids}}, {"parent": None}]},
            options={"session": session},
        )
        if root_cnt > 0:
            raise ValueError("Can not delete root nodes.")

    @validator("insert-update")
    async def v_parent_valid(self, query: MongoQuery | None, data: TreeNodeCreate | TreeNodeUpdate) -> None:
        if data.parent is None:  # No parent node is always fine
            return

        if not await self.exists(data.parent):  # Parent must exist.
            raise ValueError("Parent does not exist.")

        if isinstance(data, TreeNodeCreate):  # No more checks during creation.
            return

        matched_ids = (await self.find_ids(query)) if isinstance(data, TreeNodeUpdate) else []
        if data.parent in matched_ids:  # Self reference is forbidden.
            raise ValueError("Self-reference.")

    async def _convert_for_insert(self, data: TreeNodeCreate) -> dict[str, Any]:
        return {
            **(await super()._convert_for_insert(data)),
            "created_at": datetime.now(timezone.utc),
        }
```

With the service implementation ready, we can move on to creating the REST API.

## Routing

In `api.py`, we will use the factory pattern to create an `APIRouter` instance for the `fastapi` application:

```python
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_motor_oil import AgnosticDatabase, DatabaseProvider, DeleteError, DeleteResultModel, StrObjectId

from .model import TreeNode, TreeNodeCreate, TreeNodeUpdate
from .service import TreeNodeService

def make_api(
    *,
    get_database: DatabaseProvider,
    prefix: str = "/tree-node",
) -> APIRouter:
    """
    Tree node `APIRouter` factory.

    Arguments:
        get_database: FastAPI dependency that returns the `AgnosticDatabase`
                      database instance for the API.
        prefix: The prefix for the created `APIRouter`.

    Returns:
        The created `APIRouter` instance.
    """
    api = APIRouter(prefix=prefix)

    @api.get("/", response_model=list[TreeNode])
    async def get_all(
        database: AgnosticDatabase = Depends(get_database),
    ) -> list[dict[str, Any]]:
        svc = TreeNodeService(database)
        return [d async for d in svc.find()]

    @api.post("/", response_model=TreeNode)
    async def create(
        data: TreeNodeCreate,
        database: AgnosticDatabase = Depends(get_database),
    ) -> dict[str, Any]:
        svc = TreeNodeService(database)

        try:
            result = await svc.insert_one(data)
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Creation failed.")

        if (created := await svc.get_by_id(result.inserted_id)) is not None:
            return created

        raise HTTPException(status.HTTP_409_CONFLICT)

    @api.get("/{id}", response_model=TreeNode)
    async def get_by_id(
        id: StrObjectId,
        database: AgnosticDatabase = Depends(get_database),
    ) -> dict[str, Any]:
        svc = TreeNodeService(database)
        if (result := await svc.get_by_id(id)) is not None:
            return result

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(id))

    @api.put("/{id}", response_model=TreeNode)
    async def update_by_id(
        id: StrObjectId,
        data: TreeNodeUpdate,
        database: AgnosticDatabase = Depends(get_database),
    ) -> dict[str, Any]:
        svc = TreeNodeService(database)

        try:
            result = await svc.update_by_id(id, data)
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(id))

        if result.matched_count == 0:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(id))

        if (updated := await svc.get_by_id(id)) is not None:
            return updated

        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(id))

    @api.delete("/{id}", response_model=DeleteResultModel)
    async def delete_by_id(
        id: StrObjectId,
        database: AgnosticDatabase = Depends(get_database),
    ) -> DeleteResultModel:
        svc = TreeNodeService(database)
        try:
            result = await svc.delete_by_id(id)
        except DeleteError:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(id))
        if result.deleted_count == 0:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(id))

        return DeleteResultModel(delete_count=result.deleted_count)

    return api
```

## The application

Finally, we can create the application itself and include our routes in it:

```python
from contextlib import asynccontextmanager
from functools import lru_cache

from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

@lru_cache(maxsize=1)
def get_database() -> AsyncIOMotorDatabase:
    """Database provider dependency for the created API."""
    mongo_connection_string = "mongodb://127.0.0.1:27017"
    database_name = "tree-db"
    client = AsyncIOMotorClient(mongo_connection_string)
    return client[database_name]

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Create all indexes on startup if they don't exist already.
    from .service import TreeNodeService

    db = get_database(get_client())

    await TreeNodeService(db).create_indexes()

    yield  # Application starts

def register_routes(app: FastAPI) -> None:
    """Registers all routes of the application."""
    from .api import make_api as make_tree_node_api

    api_prefix = "/api/v1"

    app.include_router(
        make_tree_node_api(get_database=get_database),
        prefix=api_prefix,
    )

def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)  # Set lifespan method.

    register_routes(app)

    return app
```

Notice the async `lifespan()` method (context manager) that creates the declared indexes before the application starts serving requests by calling the `create_indexes()` method of each service. There are of course many other ways for adding index creation (or recreation) to an application, like database migration or command line tools. Doing it in the `lifespan` method of the application is just one, easy to implement solution that works well for relatively small databases.

## Run

With everything ready, we can start the application by executing `uvicorn tree_app.main:create_app --reload --factory` in the root directory and go to [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) to try the created REST API.
