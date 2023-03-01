# fastapi-motor-oil

Typed utilities for using MongoDB (and the async `motor` driver) with FastAPI - not an ODM.

## Installation

You can install the library and its dependencies with `pip install fastapi-motor-oil`.

## Example

Prerequisites:

- MongoDB (e.g. the Community Edition) installed and running locally;
- `fastapi` with all its dependencies (`pip install fastapi[all]`);
- This library (`pip install fastapi-motor-oil`).

In this example we will create:

- a simple `TreeNode` document model with a `name` and an optional reference to a `parent` node and some delete rules;
- the services that are necessary to create, read, update, and delete documents;
- a `fastapi` `APIRouter` factory that can be included in `fastapi` applications;
- and the `fastapi` application itself.

The project layout under your root directory will be as follows:

- `/tree_app`
  - `__init__.py`
  - `api.py`
  - `app.py`
  - `model.py`
  - `service.py`

Model definitions (in `model.py`):

```python
from fastapi_motor_oil import DocumentModel, StrObjectId
from pydantic import BaseModel

class TreeNode(DocumentModel):
    """
    Tree node document model.
    """

    name: str
    parent: StrObjectId | None

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

Service implementation (in `service.py`):

```python
from collections.abc import Sequence

from bson import ObjectId
from fastapi_motor_oil import CollectionOptions, MongoService, delete_rule, validator
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

        if isinstance(data, TreeNodeCreate):  # No more check during creation.
            return

        matched_ids = (await self.find_ids(query)) if isinstance(data, TreeNodeUpdate) else []
        if data.parent in matched_ids:  # Self reference is forbidden.
            raise ValueError("Self-reference.")
```

Routing implementation (in `api.py`):

```python
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_motor_oil import AgnosticDatabase, DatabaseProvider, DeleteResultModel, StrObjectId

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
        add_get_all: Whether to add the "get all" route to the router.
        add_create: Whether to add the "create" route to the router.
        add_get_by_id: Whether to add the "get by ID" route to the router.
        add_delete: Whether to add the "delete" route to the router.
        add_update: Whether to add the "update" route to the router.

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
        result = await svc.delete_by_id(id)
        if result.deleted_count == 0:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(id))

        return DeleteResultModel(delete_count=result.deleted_count)

    return api
```

Application (in `app.py`):

```python
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

def register_routes(app: FastAPI) -> None:
    """Registers all routes of the application."""
    from .api import make_tree_node_api

    api_prefix = "/api/v1"

    app.include_router(
        make_tree_node_api(get_database=get_database),
        prefix=api_prefix,
    )

def create_app() -> FastAPI:
    app = FastAPI()

    register_routes(app)

    return app
```

Add `__init__.py` as well to `tree_app`:

```python
from .app import create_app
```

With everything in place, you can serve the application by executing `uvicorn tree_app:create_app --reload --factory` in your root directory. Go to [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) in the browser to see and try the created REST API.

## Requirements

The project depends on `motor` (the official asyncio MongoDB driver, which is built on top of `pymongo` and `bson`) and `pydantic`.

`fastapi` is not an actual dependency, but the code was written with `fastapi` applications with a REST API in mind.

## Development

Use `black` for code formatting and `mypy` for static code analysis.

## Contributing

Contributions are welcome.

## License - MIT

The library is open-sourced under the conditions of the MIT [license](https://choosealicense.com/licenses/mit/).
