from abc import ABC, abstractmethod
from hag_logger import Logger

class Database(ABC):
    _logger = Logger("database_handler_error")
    
    @staticmethod
    @abstractmethod
    async def connect():
        raise NotImplementedError
    
    @staticmethod
    @abstractmethod
    async def close():
        raise NotImplementedError
    
    @staticmethod
    @abstractmethod
    async def select(table: str, columns: list[str], where_columns: list[str] = None, where_values: list[str] = {}, database: str = None):
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    async def table_or_database_exists(table: str = None, database: str = None):
        raise NotImplementedError
    
    @staticmethod
    @abstractmethod
    async def get_tables(database: str):
        raise NotImplementedError
    
    @staticmethod
    @abstractmethod
    async def get_columns(table_name: str, database: str = None):
        raise NotImplementedError
    
    @staticmethod
    @abstractmethod
    async def insert_or_update(table_name: str, columns: list, values: list, update_only: bool = False):
        raise NotImplementedError
    
    @staticmethod
    @abstractmethod
    async def delete(table_name: str, columns: list, values: list):
        raise NotImplementedError
