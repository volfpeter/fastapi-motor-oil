# fastapi-motor-oil

Typed utilities for using MongoDB (and the asyncio `motor` driver) with FastAPI - not an ODM.

## Installation

You can install the library and its dependencies with `pip install fastapi-motor-oil`.

## Example

Prerequisites:

- MongoDB (e.g. the Community Edition) installed and running locally;
- `fastapi` with all its dependencies (`pip install fastapi[all]`);
- This library (`pip install fastapi-motor-oil`).

In this example we will create:

- a simple `Note` document model;
- the services that are necessary to create, read, update, and delete notes;
- a `fastapi` `APIRouter` factory that can be included in `fastapi` applications;
- and the `fastapi` application itself.

The project layout under your root directory will be as follows:

- `/notes_app`
  - `__init__.py`
  - `api.py`
  - `app.py`
  - `model.py`
  - `service.py`

Model definitions (in `model.py`):

```python
from fastapi_motor_oil import DocumentModel, UTCDatetime
from pydantic import BaseModel

class Note(DocumentModel):
    """Model for serializing documents."""
    title: str
    text: str
    created_at: UTCDatetime

class NoteCreationData(BaseModel):
    """Model for creating documents."""
    title: str
    text: str

class NoteUpdateData(BaseModel):
    """Model for updating documents."""
    title: str | None = None
    text: str | None = None
```

Service implementation (in `service.py`):

```python
from typing import Any

from fastapi_motor_oil import AsyncIOMotorDatabase, MongoService
from datetime import datetime

from .model import NoteCreationData, NoteUpdateData

class NoteService(MongoService[NoteCreationData, NoteUpdateData]):
    __slots__ = ()

    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        super().__init__(database, "notes")

    def _prepare_for_insert(self, data: NoteCreationData) -> dict[str, Any]:
        return {
            **super()._prepare_for_insert(data),
            "created_at": datetime.utcnow(),  # Insert the created_at attribute.
        }

```

Routing implementation (in `api.py`):

```python
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_motor_oil import (
    AsyncIOMotorDatabase,
    DatabaseProvider,
    DeleteResultModel,
    StrObjectId,
)

from .model import Note, NoteCreationData, NoteUpdateData
from .service import NoteService

def make_notes_api(
    *,
    get_database: DatabaseProvider,
    prefix: str = "/note",
) -> APIRouter:
    """
    Note `APIRouter` factory.

    Arguments:
        get_database: FastAPI dependency that returns the `AsyncIOMotorDatabase`
                      database instance for the API.
        prefix: The prefix for the created `APIRouter`.

    Returns:
        The created `APIRouter` instance.
    """
    api = APIRouter(prefix=prefix)

    @api.get("/", response_model=list[Note])
    async def get_all(
        database: AsyncIOMotorDatabase = Depends(get_database),
    ) -> list[dict[str, Any]]:
        svc = NoteService(database)
        return [d async for d in svc.find()]  # This async for can be quite inefficient...

    @api.post("/", response_model=Note)
    async def create(
        data: NoteCreationData,
        database: AsyncIOMotorDatabase = Depends(get_database),
    ) -> dict[str, Any]:
        svc = NoteService(database)
        result = await svc.insert_one(data)
        if (created := await svc.get_by_id(result.inserted_id)) is not None:
            return created

        raise HTTPException(status.HTTP_409_CONFLICT)

    @api.get("/{id}", response_model=Note)
    async def get_by_id(
        id: StrObjectId,
        database: AsyncIOMotorDatabase = Depends(get_database),
    ) -> dict[str, Any]:
        svc = NoteService(database)
        if (result := await svc.get_by_id(id)) is not None:
            return result

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(id))

    @api.put("/{id}", response_model=Note)
    async def update_by_id(
        id: StrObjectId,
        data: NoteUpdateData,
        database: AsyncIOMotorDatabase = Depends(get_database),
    ) -> dict[str, Any]:
        svc = NoteService(database)
        result = await svc.update_by_id(id, data)
        if result.matched_count == 0:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(id))

        if (updated := await svc.get_by_id(id)) is not None:
            return updated

        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(id))

    @api.delete("/{id}", response_model=DeleteResultModel)
    async def delete_by_id(
        id: StrObjectId,
        database: AsyncIOMotorDatabase = Depends(get_database),
    ) -> DeleteResultModel:
        svc = NoteService(database)
        result = await svc.delete_by_id(id)
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
    database_name = "notes-database"
    client = AsyncIOMotorClient(mongo_connection_string)
    return client[database_name]

def register_routes(app: FastAPI) -> None:
    """Registers all routes of the application."""
    from .api import make_notes_api

    api_prefix = "/api/v1"

    app.include_router(
        make_notes_api(get_database=get_database),
        prefix=api_prefix,
    )

def create_app() -> FastAPI:
    app = FastAPI()

    register_routes(app)

    return app
```

Add `__init__.py` as well to `notes_app`:

```python
from .app import create_app
```

With everything in place, you can serve the application by executing `uvicorn notes_app:create_app --reload --factory` in your root directory. Go to [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) in the browser to see and try the created REST API.

## Requirements

The project depends on `motor` (the official asyncio MongoDB driver, which is built on top of `pymongo` and `bson`) and `pydantic`.

`fastapi` is not an actual dependency, but the code was written with `fastapi` applications with a REST API in mind.

## Development

Use `black` for code formatting and `mypy` for static code analysis.

## Contributing

Contributions are welcome.

## License - MIT

The library is open-sourced under the conditions of the MIT [license](https://choosealicense.com/licenses/mit/).
