import json
            
class Database:
    _pool = None
    with open('config.json') as f:
        config = json.load(f)
        match config['database']:
            case "postgres":
                from postgres import Postgres
                database = Postgres
            case "mongodb":
                from mongodb import MongoDB
                database = MongoDB
    
    @staticmethod
    async def connect():
        await Database.database.connect()
        
    @staticmethod
    async def close():
        await Database.database.close()
    
    @staticmethod
    async def select(_, *args):
        try:
            return await Database.database.select(*args)
        except Exception as e:
            Database._logger.error(e)
            return None, False

    @staticmethod
    async def table_or_database_exists(_, table: str = None, database: str = None):
        try:
            return await Database.database.table_or_database_exists(table, database)
        except Exception as e:
            Database._logger.error(e)
            return None, False

    @staticmethod
    async def get_tables(_, database: str):
        try:
            return await Database.database.get_tables(database)
        except Exception as e:
            Database._logger.error(e)
            return None, False

    @staticmethod
    async def get_columns(_, table_name: str, database: str = None):
        try:
            return await Database.database.get_columns(table_name, database)
        except Exception as e:
            Database._logger.error(e)
            return None, False
    
    @staticmethod
    async def insert_or_update(_, *args):
        try:
            return await Database.database.insert_or_update(*args)
        except Exception as e:
            Database._logger.error(e)
            return None, False

    @staticmethod
    async def delete(_, *args):
        try:
            return await Database.database.delete(*args)
        except Exception as e:
            Database._logger.error(e)
            return None, False