from app.storage.postgres import PostgresStorage
from app.storage.settings import StorageType, settings
from app.storage.sqlite import SqliteStorage

if settings.storage_type == StorageType.SQLITE:
    storage = SqliteStorage()
elif settings.storage_type == StorageType.POSTGRES:
    storage = PostgresStorage()
else:
    raise NotImplementedError()
