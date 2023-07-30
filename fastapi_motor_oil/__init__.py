from warnings import warn

from .bound_method_wrapper import BoundMethodWrapper as BoundMethodWrapper
from .delete_rule import DeleteConfig as DeleteConfig
from .delete_rule import DeleteError as DeleteError
from .delete_rule import delete_rule as delete_rule
from .model import AgnosticClient as AgnosticClient
from .model import AgnosticDatabase as AgnosticDatabase
from .model import ClientProvider as ClientProvider
from .model import DatabaseProvider as DatabaseProvider
from .model import DeleteResultModel as DeleteResultModel
from .model import DocumentModel as DocumentModel
from .model import StrObjectId as StrObjectId
from .model import UTCDatetime as UTCDatetime
from .service import DeleteResult as DeleteResult
from .service import InsertOneResult as InsertOneResult
from .service import MongoService as MongoService
from .service import UpdateResult as UpdateResult
from .typing import AgnosticCollection as AgnosticCollection
from .typing import Collation as Collation
from .typing import CollectionOptions as CollectionOptions
from .typing import DeleteOptions as DeleteOptions
from .typing import FindOptions as FindOptions
from .typing import IndexData as IndexData
from .typing import InsertOneOptions as InsertOneOptions
from .typing import MongoProjection as MongoProjection
from .typing import MongoQuery as MongoQuery
from .typing import UpdateManyOptions as UpdateManyOptions
from .typing import UpdateObject as UpdateObject
from .typing import UpdateOneOptions as UpdateOneOptions
from .validator import ValidationError as ValidationError
from .validator import Validator as Validator
from .validator import validator as validator

warn(
    "FastAPI-motor-oil is deprecated and replaced by motorhead with support for Pydantic v2. See https://volfpeter.github.io/motorhead/",
    DeprecationWarning,
    stacklevel=2,
)
