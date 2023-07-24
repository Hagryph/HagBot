from database_handler_client import Client
from master import Master
import json

class Slave:
    async def start(self):
        with open('config.json') as f:
            config = json.load(f)
            master_config = config['master']
            self._client = Client(master_config['host'], master_config['port'], 1, 1)
            slave_config = config['slave']
            json_data = json.dumps({"function_name": "create_client", "args": (slave_config['port'], slave_config['minimum_pool_size'], slave_config['maximum_pool_size'])})
            await self._client.send_message(json_data)
        await self._client.close()
        self._master = Master()
        print("Slave started")
        await self._master.start(slave_config['host'], slave_config['port'], True)