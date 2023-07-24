import asyncio, json, threading
from contextlib import asynccontextmanager
from hag_logger import Logger

class TimeoutError(Exception):
    def __init__(self, message="Operation timed out."):
        self.message = message
        super().__init__(self.message)

class Connection:
    _logger = Logger("connection_error")

    def __init__(self, host: str, port: int):
        self._ready = True
        self._host = host
        self._port = port
        self._reader = None
        self._writer = None
        
    async def _create_connection(self):
        while True:
            try:
                self._reader, self._writer = await asyncio.open_connection(self._host, self._port)
                self._ready = True
                break
            except Exception as e:
                self._logger.log(f"An error occurred while creating the connection: {e}")
                await asyncio.sleep(5)
                continue
            
    async def send_message(self, message: str):
        result, success = None, False
        while True:
            try:
                while not self._ready:
                    pass
                self._writer.write(message.encode())
                self._writer.write_eof()
                result = await self._reader.read()
                result, success = json.loads(result.decode())
            except Exception:
                self._ready = False
                await self._create_connection()
                continue
            return result, success
    
    def close(self):
        try:
            self._writer.close()
        except:
            pass
        
class ConnectionPool:
    def __init__(self, host: str, port: int, pool_size: int = 20, max_pool_size: int = 100):
        self._host = host
        self._port = port
        self._pool_size = pool_size
        self._max_pool_size = max_pool_size
        self._connections_created = 0
        self._connections = asyncio.Queue()
        self._closed = False
        t = threading.Thread(target=self._handle_connections)
        t.start()
        
    def _handle_connections(self):
        self._loop = asyncio.new_event_loop()
        self._loop.create_task(self._create_initial_connections())
        self._loop.run_forever()
        
    async def _create_initial_connections(self):
        tasks = []
        for _ in range(self._pool_size):
            task = asyncio.create_task(self._create_connection())
            tasks.append(task)
            
        await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)

    async def _create_connection(self):
        connection = Connection(self._host, self._port)
        self._connections_created += 1
        await self._connections.put(connection)
        
    async def return_connection(self, connection: Connection):
        await self._connections.put(connection)
        
    @asynccontextmanager
    async def get_connection(self):
        if self._connections.empty() and self._connections_created < self._max_pool_size:
            await self._create_connection()
        try:
            connection = await self._connections.get()
            yield connection
        finally:
            if connection and not self._closed:
                await self.return_connection(connection)
            elif connection and self._closed:
                await connection.close()
                
    async def close(self):
        self._closed = True
        while not self._connections.empty():
            connection = await self._connections.get()
            connection.close()
        self._loop.stop()

class Client:
    def __init__(self, host: str, port: int, pool_size: int = 20, max_pool_size: int = 100):
        self._connection_pool = ConnectionPool(host, port, pool_size, max_pool_size)
        
    async def send_message(self, message: str, timeout: float = 0):
        async with self._connection_pool.get_connection() as connection:
            if timeout > 0:
                try:
                    return await asyncio.wait_for(connection.send_message(message), timeout)
                except asyncio.TimeoutError:
                    raise TimeoutError()
            else:
                return await connection.send_message(message)
        
    async def close(self):
        await self._connection_pool.close()