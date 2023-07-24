from app import views
from backend.database import Database
from backend.account import Account
from hag_logger import Logger
import asyncio, sys

async def initialize():
        user_ids, success = await Database.get_all_user_ids()
        if not success:
            _logger.log("Error occured while initializing accounts")
            sys.exit()

        for user_id in user_ids:
            account = Account(user_id)
            access_token = await account.get_access_token()
            if access_token:
                views.users[user_id] = (account)
                
_logger = Logger("init_error.txt");
asyncio.run(initialize())