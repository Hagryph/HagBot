from contextlib import asynccontextmanager
from blueprints import Database
import asyncpg, json, os

class TableConfig:
    def __init__(self, name: str, database: str, columns: dict, primary_key: list, auto_increment_keys: list = [], foreign_keys: list = {}, default_values: dict = {}):
        self.name = name
        self.database = database
        self.columns = columns
        self.primary_key = primary_key
        self.auto_increment_keys = auto_increment_keys or []
        self.foreign_keys = foreign_keys or []
        self.default_values = default_values or {}

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
            cp._pools[configuration.database] = await asyncpg.create_pool(
                user=configuration.user, password=configuration.password,
                host=configuration.host, port=configuration.port, database=configuration.database,
                min_size=configuration.minimum_pool_size, max_size=configuration.maximum_pool_size
            )
        cp._tables = {}
        return cp

    async def load_tables(self):
        self._tables = {database: (await Postgres.get_tables(database))[0] for database in self._pools.keys()}

    def table_or_database_exists(self, table_name: str = None, database: str = None):
        if database is None:
            database = self.find_database_for_table(table_name)
        return database in self._tables.keys()
       
    def find_database_for_table(self, table_name: str):
        for database, tables in self._tables.items():
            if table_name in tables:
                return database
        return None

    def close(self):
        for pool in self._pools.values():
            pool.close()

    @asynccontextmanager
    async def acquire(self, database: str = None, table_name: str = None):
        if database is None and table_name is not None:
            database = self.find_database_for_table(table_name)
        if database is None or database not in self._pools.keys():
            raise ValueError("No or false database provided")
        async with self._pools[database].acquire() as conn:
            yield conn
            
class Postgres(Database):
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
                tables = []
                for table in database['tables']:
                    tables.append(TableConfig(
                        name=table['name'],
                        database=database['name'],
                        columns=table['columns'],
                        primary_key=table['primary_key'],
                        auto_increment_keys=table.get('auto_increment_keys') or [],
                        foreign_keys=table.get('foreign_keys') or [],
                        default_values=table.get('default_values') or {}
                    ))
                databases.append({'name': database['name'], 'connection_pool_config': connection_pool_config, 'tables': tables})

            Postgres._pool = await ConnectionPool.create_pool([database['connection_pool_config'] for database in databases])
            await Postgres._create_tables(databases)
            await Postgres._pool.load_tables()
        except Exception as e:
            Postgres._logger.log(f"An error occurred while loading the config file or creating the connections: {e}")
            os._exit(1)
        
    @staticmethod
    async def close():
        await Postgres._pool.close()

    @staticmethod
    async def _execute(query: str, database: str = None, table_name: str = None, *args: tuple):
        try:
            async with Postgres._pool.acquire(database, table_name) as conn:
                return await conn.fetch(query, *args), True
        except Exception as e:
            Postgres._logger.log(f"An error occurred while executing this query: {query}\n{e}")
            return None, False

    @staticmethod
    async def select(table: str, columns: list[str], where_columns: list[str] = None, where_values: list[str] = {}, database: str = None):
        query = f"SELECT {', '.join(columns)} FROM {table}"
        if where_columns:
            query += " WHERE " + " AND ".join([f"{column} = ${i+1}" for i, column in enumerate(where_columns)])
        return await Postgres._execute(query, database, table, *where_values)

    @staticmethod
    async def table_or_database_exists(table_name: str = None, database: str = None):
        return Postgres._pool.table_or_database_exists(table_name, database)
    
    @staticmethod
    async def get_tables(database: str):
        tables = []
        rows, success = await Postgres.select("pg_tables", ["tablename"], ["schemaname"], ['public'], database)
        if success:
            for row in rows:
                tables.append(row[0])
        return tables, success

    @staticmethod
    async def get_columns(table_name: str, database: str = None):
        columns = []
        rows, success = await Postgres.select("information_schema.columns", ["*"], ["table_name"], [table_name], database)
        if success:
            for row in rows:
                columns.append(row)
        return columns, success

    @staticmethod
    async def _drop_all_foreign_keys(database_name):
        rows, success = await Postgres.select("information_schema.table_constraints", ["table_name", "constraint_name"], ["constraint_type"], ["FOREIGN KEY"], database_name)
        if not success:
            return success
        for row in rows:
            drop_query = f"ALTER TABLE {row[0]} DROP CONSTRAINT {row[1]}"
            _, success = await Postgres._execute(drop_query, database_name)
            if not success:
                return success
        return success
            
    @staticmethod
    async def _prepare_tables(database_name):
        return await Postgres._drop_all_foreign_keys(database_name)

    @staticmethod
    async def _adjust_primary_keys(database: str, table_name: str, primary_keys: list):
        query = f"ALTER TABLE {table_name} DROP CONSTRAINT IF EXISTS {table_name}_pkey"
        result, success = await Postgres._execute(query, database)
        if not success:
            return result, success
        query = f"ALTER TABLE {table_name} ADD PRIMARY KEY({', '.join(primary_keys)})"
        return await Postgres._execute(query, database)

    @staticmethod
    async def _adjust_foreign_keys(database: str, table_name: str, foreign_keys: dict):
        success = True
        for fk in foreign_keys:
            keys, fk_table, columns = fk["keys"], fk["table"], fk["columns"]
            query = f"ALTER TABLE {table_name} ADD FOREIGN KEY ({', '.join(keys)}) REFERENCES {fk_table}({', '.join(columns)})"
            _, success = await Postgres._execute(query, database)
            if not success:
                return success
        return success
    
    @staticmethod
    def _get_default_value(data_type: str):
        if data_type in ("INTEGER", "SMALLINT", "BIGINT", "SERIAL", "BIGSERIAL", "REAL", "DOUBLE PRECISION", "NUMERIC", "DECIMAL"):
            return 0
        elif data_type in ("CHAR", "VARCHAR", "TEXT", "CITEXT", "NAME", "BPCHAR"):
            return "''"
        elif data_type in ("BOOLEAN"):
            return "FALSE"
        elif data_type in ("DATE", "TIME", "TIMETZ", "TIMESTAMP", "TIMESTAMPTZ"):
            return "NOW()"
        elif data_type in ("ARRAY", "ENUM", "RANGE"):
            return "DEFAULT"
        else:
            return "NULL"

    @staticmethod
    async def _alter_table(table: TableConfig):
        existing_columns, _ = await Postgres.get_columns(table.name, table.database)
        existing_columns = [col["column_name"] for col in existing_columns]
        column_strs = []
        for column_name, data_type in table.columns.items():
            default_value = ""
            if column_name in table.auto_increment_keys:
                default_value = f"nextval('{table.name}_{column_name}_seq'::regclass)"
            elif column_name in table.default_values:
                default_value = table.default_values[column_name]
            else:
                default_value = Postgres._get_default_value(data_type)
                
            if column_name not in existing_columns:
                column_str = f"ADD COLUMN "
                column_str += f"{column_name} {data_type} NOT NULL DEFAULT "
                column_str += f"{default_value}"
            else:
                column_str = "ALTER COLUMN "
                column_str += f"{column_name} SET DATA TYPE {data_type} NOT NULL, "
                column_str = "ALTER COLUMN "
                column_str += f"{column_name} SET NOT NULL, "
                column_str += f"ALTER COLUMN {column_name} SET DEFAULT "
                column_str += f"{default_value}"
            column_strs.append(column_str)

        for column_name in existing_columns:
            if column_name not in table.columns:
                column_str = f"DROP COLUMN {column_name}"
                column_strs.append(column_str)
            
        query = f"ALTER TABLE {table.name} {', '.join(column_strs)}"
        _, success = await Postgres._execute(query, table.database)
        if success:
            _, success = await Postgres._adjust_primary_keys(table.database, table.name, table.primary_key)
        if success:
            success = await Postgres._adjust_foreign_keys(table.database, table.name, table.foreign_keys)

        return success
    
    @staticmethod
    async def _create_table(table: TableConfig):
        existing_tables, _ = await Postgres.get_tables(table.database)
        
        if table.name in existing_tables:
            success = await Postgres._alter_table(table)
        else:
            column_strs = []
            for column_name, data_type in table.columns.items():
                column_str = f"{column_name} {data_type} NOT NULL"
                if column_name in table.auto_increment_keys:
                    column_str += f" DEFAULT nextval('{table.name}_{column_name}_seq'::regclass)"
                elif column_name in table.default_values:
                    column_str += f" DEFAULT {table.default_values[column_name]}"
                else:
                    default_value = Postgres._get_default_value(data_type)
                    column_str += f" DEFAULT {default_value}"
                column_strs.append(column_str)

            primary_key_str = ', '.join(table.primary_key)
            foreign_key_strs = []
            for fk in table.foreign_keys:
                keys, fk_table, columns = fk["keys"], fk["table"], fk["columns"]
                foreign_key_str = f"FOREIGN KEY ({', '.join(keys)}) REFERENCES {fk_table}({', '.join(columns)})"
                foreign_key_strs.append(foreign_key_str)
            column_strs += foreign_key_strs

            query = f"CREATE TABLE {table.name} ({', '.join(column_strs)}, PRIMARY KEY({primary_key_str}))"
            _, success = await Postgres._execute(query, table.database)

        return success
    
    @staticmethod
    async def _create_tables(databases: list[dict[str, any]]):
        for db_config in databases:
            db_name = db_config['name']
            tables = db_config['tables']
            success = await Postgres._prepare_tables(db_name)
            if not success:
               os.exit(1)
            for table in tables:
                success = await Postgres._create_table(table)
                if not success:
                   os.exit(1)

    @staticmethod
    async def _entry_exists(table_name: str, columns: list, values: list):
        query = f"SELECT EXISTS(SELECT 1 FROM {table_name} WHERE {' AND '.join([f'{column} = ${i+1}' for i, column in enumerate(columns)])})"
        response = await Postgres._execute(query, None, table_name, *values)
        if response[1] and len(response[0]) > 0:
            return response[0][0]["exists"]
        return False
    
    @staticmethod 
    async def _get_primary_keys(database: str, table_name: str):
        response = await Postgres.select("information_schema.table_constraints", ["constraint_name"], ["table_name", "constraint_type"], [table_name, "PRIMARY KEY"], database)
        if response[1] and len(response[0]) == 1:
            response = await Postgres.select("information_schema.key_column_usage", ["column_name"], ["constraint_name"], response[0][0], database)
            if response[1]:
                return response[0]
        return []
    
    @staticmethod
    async def _insert(table_name: str, columns: list, values: list):
        placeholders = ", ".join([f'${i+1}' for i in range(len(values))])
        query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
        return await Postgres._execute(query, None, table_name, *values)
        
    @staticmethod
    async def _update(table_name: str, columns: list, values: list):
        database = Postgres._pool.find_database_for_table(table_name)
        primary_keys = await Postgres._get_primary_keys(database, table_name)
        primary_keys = [pk[0] for pk in primary_keys]
        update_query = f"UPDATE {table_name} SET {', '.join([f'{column} = ${i+1}' for i, column in enumerate(columns)])} WHERE {' AND '.join([f'{pk} = ${len(columns) + i+1}' for i, pk in enumerate(primary_keys)])}"
        return await Postgres._execute(update_query, None, table_name, *(values + [values[columns.index(pk)] for pk in primary_keys]))
    
    @staticmethod
    async def insert_or_update(table_name: str, columns: list, values: list, update_only: bool = False):
        database = Postgres._pool.find_database_for_table(table_name)
        primary_keys = await Postgres._get_primary_keys(database, table_name)
        primary_keys = [pk[0] for pk in primary_keys]
        primary_key_values = {pk: values[columns.index(pk)] for pk in primary_keys if pk in columns}
        
        if len(columns) != len(values):
            return False
        entry_exists = await Postgres._entry_exists(table_name, primary_key_values.keys(), primary_key_values.values())
        if entry_exists:
            return await Postgres._update(table_name, columns, values)
        elif not update_only:
            return await Postgres._insert(table_name, columns, values)

        return None, False

    @staticmethod
    async def delete(table_name: str, columns: list, values: list):
        query = f"DELETE FROM {table_name} WHERE {' AND '.join([f'{column} = ${i+1}' for i, column in enumerate(columns)])}"
        return await Postgres._execute(query, None, table_name, *values)