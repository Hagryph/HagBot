import asyncio, json, socket
from database_handler import Database
from helper import make_serializable, convert_iso_format_to_datetime
from database_handler_client import Client, TimeoutError
from api import API
        
class Master:
    def __init__(self):
        self._server = None
        self._clients = []
        self._message_linker = {
            "select": Database.select,
            "update": Database.insert_or_update,
            "delete": Database.delete,
            "tables": Database.get_tables,
            "columns": Database.get_columns,
            "create_client": self.create_client,
        }

    async def start(self, host: str = None, port: str = None, slave: bool = False):
        await Database.connect()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        with open('config.json') as f:
            config = json.load(f)
            host, port = host or config['master']['host'], port or config['master']['port']
            print(f"Starting server on {host}:{port}")
            sock.bind((host, port))
        self._server = await asyncio.start_server(self._handle_connection, sock=sock)
        if not slave:
            API.run(config['api']['host'], config['api']['port'], self)
            print("Master started")
        await self._server.serve_forever()
        await self._close()

    async def execute(self, json_string: str, connection = None):
        deserialized = json.loads(json_string)
        function_name = deserialized["function_name"]
        args = convert_iso_format_to_datetime(deserialized["args"])
        result = await self._message_linker[function_name](connection, *args)
        if result[1] == False:
            result = await self._find_slave(json_string)
        result = make_serializable(result)

        return json.dumps(result)
        
    async def _handle_connection(self, reader, writer):
        try:
            query = (await reader.read()).decode()
        except:
            return
        connection = (reader, writer)
        result_string = await self.execute(query, connection)
        try:
            writer.write(result_string.encode())
            writer.write_eof()
            await writer.drain()
        except:
            return

    async def create_client(self, connection, port: int, min_pool_size: int = 20, max_pool_size: int = 100):
        _, writer = connection
        host, _ = writer.get_extra_info('peername')
        self._clients.append(Client(host, port, min_pool_size, max_pool_size))
        return None, True
        
    async def _find_slave(self, request: str):
        for client in self._clients:
            try:
                result = await client.send_message(request, 10)
                if result[1]:
                    return result
            except TimeoutError:
                await client.close()
                self._clients.remove(client)

        return None, False

    async def _close(self):
        await self._server.close()
        await self._server.wait_closed()
        await Database.close()