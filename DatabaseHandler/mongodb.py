from contextlib import asynccontextmanager
from blueprints import Database as DB
from pymongo import MongoClient
from pymongo.errors import CollectionInvalid
from pymongo.collection import Collection
import json, os

class CollectionConfig:
    def __init__(self, name: str, database: str):
        self.name = name
        self.database = database

class ConnectionPoolConfiguration:
    def __init__(self, host: str, port: int, database: str, user: str, password: str, minimum_pool_size: int, maximum_pool_size: int):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.minimum_pool_size = minimum_pool_size
        self.maximum_pool_size = maximum_pool_size
        
class ConnectionPool:
    @staticmethod
    async def create_pool(configurations: list[ConnectionPoolConfiguration]):
        cp = ConnectionPool()
        cp._pools = {}
        for configuration in configurations:
            client = MongoClient(
                host=f"mongodb://{configuration.user}:{configuration.password}@{configuration.host}:{configuration.port}/?authMechanism=DEFAULT",
                minPoolSize=configuration.minimum_pool_size,
                maxPoolSize=configuration.maximum_pool_size
            )
            cp._pools[configuration.database] = client.get_database(configuration.database)
        cp._tables = {}
        return cp

    async def load_tables(self):
        self._collections = {database: (await MongoDB.get_tables(database))[0] for database in self._pools.keys()}
       
    def find_database_for_collection(self, collection_name: str):
        for database, collection in self._collections.items():
            if collection_name in collection:
                return database
        return None 

    def close(self):
        for pool in self._pools.values():
            pool.client.close()
            
    @asynccontextmanager
    async def acquire(self, database: str = None, collection_name: str = None):
        if database is None and collection_name is not None:
            database = self.find_database_for_collection(collection_name)
        if database is None or database not in self._pools.keys():
            raise ValueError("No or false database/table provided")
        if collection_name:
            yield self._pools[database].get_collection(collection_name)
        else:
            yield self._pools[database]
            
class MongoDB(DB):
    @staticmethod
    async def connect():
        try:
            with open('config.json') as f:
                config = json.load(f)

            databases = []
            for database in config['databases']:
                connection_pool_config = ConnectionPoolConfiguration(
                    host=database['config']['host'],
                    port=database['config']['port'],
                    database=database['name'],
                    user=database['config']['user'],
                    password=database['config']['password'],
                    minimum_pool_size=database['config']['minimum_pool_size'],
                    maximum_pool_size=database['config']['maximum_pool_size']
                )
                collections = []
                for collection in database['collections']:
                    collections.append(CollectionConfig(collection['name'], database['name']))
                databases.append({'name': database['name'], 'connection_pool_config': connection_pool_config, 'collections': collections})
                
            MongoDB._pool = await ConnectionPool.create_pool([database['connection_pool_config'] for database in databases])
            await MongoDB._create_collections(databases)
            await MongoDB._pool.load_tables()
        except Exception as e:
            MongoDB._logger.log(f"An error occurred while loading the config file or creating the connections: {e}")
            os._exit(1)
        
    @staticmethod
    async def close():
        MongoDB._pool.close()

    @staticmethod
    async def select(collection_name: str, columns: list[str], where_columns: list[str] = None, where_values: list[str] = {}):
        try:
            async with MongoDB._pool.acquire(collection_name=collection_name) as collection:
                document = {where_columns[i-1]: where_values[i-1] for i in range(len(where_columns))}
                result = collection.find(document)
                result = [{column: document.get(column) for column in columns} for document in result]
            return result, True
        except:
            MongoDB._logger.log(f"An error occurred while selecting from the table {collection_name}")
            return None, False

    @staticmethod
    async def table_or_database_exists(table: str = None, database: str = None):
        pass
    
    @staticmethod
    async def get_tables(database: str):
        try:
            async with MongoDB._pool.acquire(database) as db:
                return db.list_collection_names(), True
        except:
            MongoDB._logger.log(f"An error occurred while getting the tables from the database {database}")
            return None, False

    @staticmethod
    async def get_columns(table_name: str, database: str = None):
        pass

    @staticmethod
    async def _create_collection(collection: CollectionConfig):
        try:
            async with MongoDB._pool.acquire(collection.database) as db:
                await db.create_collection(collection.name, check_exists=True)
                return True
        except CollectionInvalid:
            return True
        except:
            MongoDB._logger.log(f"An error occurred while creating the collection {collection.name} in the database {collection.database}")
            return False

    @staticmethod
    async def _create_collections(databases: list[dict[str, any]]):
        for db_config in databases:
            collections = db_config['collections']
            for collection in collections:
                success = await MongoDB._create_collection(collection)
                if not success:
                    os._exit(1)
            
    @staticmethod
    async def insert_or_update(collection_name: str, columns: list, values: list):
        try:
            async with MongoDB._pool.acquire(collection_name=collection_name) as collection:
                document = {columns[i]: values[i] for i in range(len(columns))}
                collection.insert_one(document)
                return None, True
        except:
            MongoDB._logger.log(f"An error occurred while inserting into the table {collection_name}")
            return None, False

    @staticmethod
    async def delete(table_name: str, columns: list, values: list):
        try:
            async with MongoDB._pool.acquire(collection_name=table_name) as collection:
                document = {columns[i]: values[i] for i in range(len(columns))}
                collection.delete_many(document)
                return None, True
        except:
            MongoDB._logger.log(f"An error occurred while deleting from the table {table_name}")
            return None, False