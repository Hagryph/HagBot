import uvicorn, json, asyncio
from fastapi import FastAPI
from typing import List, Any
from threading import Thread

class API:
    _app = FastAPI()

    @staticmethod
    def run(host: str, port: int, master):
        API._master = master
        API._loop = asyncio.get_running_loop()
        Thread(target=API._start, args=(host, port)).start()

    @staticmethod
    def _start(host: str, port: int):
        API._loop.create_task(uvicorn.run(API._app, host=host, port=port, log_level="warning"))
        
    @_app.get("/execute/{function_name}")
    @staticmethod
    def execute(function_name: str, args: str):
        args_list: List[Any] = json.loads(args)
        json_string = json.dumps({"function_name": function_name, "args": args_list})
        result = asyncio.run_coroutine_threadsafe(API._master.execute(json_string), API._loop).result()
        return result