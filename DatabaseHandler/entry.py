from hag_logger import Logger
import asyncio, json

if __name__ == '__main__':
    logger = Logger("entry_error")
    try:
        with open('config.json') as f:
            config = json.load(f)
            mode = config['mode']
            match mode.lower():
                case 'master':
                    from master import Master
                    module = Master()
                case 'slave':
                    from slave import Slave
                    module = Slave()
                case _:
                    print(f"Module {mode.capitalize()} not found")
        print(f"Starting module: {mode.capitalize()}")
        asyncio.run(module.start())
    except Exception as e:
        logger.log(f"Error occured while starting module: {e}")