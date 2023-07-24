import secrets, json
from hag_logger import Logger
from database_handler_client import Client

class Database:
    _logger = Logger("database_error")
    with open("client.json", "r") as f:
        client_data = json.load(f)
        _client = Client(client_data["host"], client_data["port"])
        client_data = None
    
    @staticmethod
    async def _execute(function_name, *args):
        json_data = json.dumps({"function_name": function_name, "args": args})
        response = await Database._client.send_message(json_data)
        if not response[1]:
            Database._logger.log("request not successful")
        return response 

    @staticmethod
    async def select(table_name, columns, where_columns = None, where_values = {}):
        return await Database._execute("select", table_name, columns, where_columns, where_values)
    
    @staticmethod
    async def update(table_name, columns, values, update_only = False):
        return await Database._execute("update", table_name, columns, values, update_only)

    @staticmethod
    async def delete(table_name, where_columns, where_values):
        return await Database._execute("delete", table_name, where_columns, where_values)

    @staticmethod
    async def tables():
        return await Database._execute("tables", "twitch")
    
    @staticmethod
    async def columns(table_name):
        return await Database._execute("columns", table_name, "twitch")
       
    @staticmethod
    async def create_account(id, username, access_token, refresh_token):
        return await Database.update("accounts", ["id", "username", "access_token", "refresh_token"], [id, username, access_token, refresh_token])

    @staticmethod
    async def activate_account(id):
        response = await Database.update("accounts", ["id", "is_active"], [id, 1], True)
        return response[1]
    
    @staticmethod
    async def deactivate_account(id):
        response = await Database.update("accounts", ["id", "is_active"], [id, 0], True)
        return response[1]
        
    @staticmethod
    async def is_active(id):
        response = await Database.select("accounts", ["is_active"], ["id"], [id])
        if response[1] and len(response[0]) > 0:
            return response[0][0]["is_active"]
        return False

    @staticmethod
    async def get_role(id):
        response = await Database.select("accounts", ["role_id"], ["id"], [id])
        if response[1] and len(response[0]) > 0:
            return response[0][0]["role_id"]
        return None

    @staticmethod
    async def get_username(id):
        response = await Database.select("accounts", ["username"], ["id"], [id])
        if response[1] and len(response[0]) > 0:
            return response[0][0]["username"]
        return None

    @staticmethod
    async def save_config(id, column, value):
        response = await Database.update("config", ["id", column], [id, value])
        return response[1]

    @staticmethod
    async def get_config(id, column):
        response = await Database.select("config", [column], ["id"], [id])
        if response[1] and len(response[0]) > 0:
            return response[0][0][column]
        return None
        
    @staticmethod
    async def get_access_token(user_id):
        response = await Database.select("accounts", ["access_token"], ["id"], [user_id])
        if response[1] and len(response[0]) > 0:
            return response[0][0]["access_token"]
        return None

    @staticmethod
    async def update_access_token(id, access_token):
        response = await Database.update("accounts", ["id", "access_token"], [id, access_token])
        return response[1]
        
    @staticmethod
    async def get_refresh_token(id):
        response = await Database.select("accounts", ["refresh_token"], ["id"], [id])
        if response[1] and len(response[0]) > 0:
            return response[0][0]["refresh_token"]
        return None
    
    @staticmethod
    async def get_all_user_ids():
        response = await Database.select("accounts", ["id"])
        if response[1]:
            return [user_id["id"] for user_id in response[0]], True
        return None, False
        
    @staticmethod
    async def create_session(id, response, session_data):
        session_key = secrets.token_hex(16)
        session_data_string = json.dumps(session_data)
        result = await Database.update("sessions", ["id", "session_key", "data"], [id, session_key, session_data_string])
        result = result[1]
        if result:
            response.set_cookie("session_key", session_key, httponly=True)
        return response

    @staticmethod
    async def delete_session(id):
        response = await Database.delete("sessions", ["id"], [id])
        return response[1]

    @staticmethod
    async def get_session(id):
        response = await Database.select("sessions", ["session_key"], ["id"], [id])
        if response[1] and len(response[0]) > 0:
            return response[0][0]["session_key"]
        return None

    @staticmethod
    async def session_exists(session_key):
        response = await Database.select("sessions", ["id"], ["session_key"], [session_key])
        if response[1] and len(response[0]) > 0:
            return True
        return False
    
    @staticmethod
    async def get_id_from_session_key(session_key):
        response = await Database.select("sessions", ["id"], ["session_key"], [session_key])
        if response[1] and len(response[0]) > 0:
            return response[0][0]["id"]
        return None
    
    @staticmethod
    async def get_data(session_key, key):
        response = await Database.select("sessions", ["data"], ["session_key"], [session_key])
        if response[1]:
            data = json.loads(response[0][0]["data"])
            return data.get(key)
        return None

    @staticmethod
    async def save_question(id: int, account_id: int, question: str):
        response = await Database.update("faq", ["id", "account_id", "question"], [id, account_id, question])
        return response[1]

    @staticmethod
    async def delete_question(id: int, account_id: int):
        response = await Database.delete("faq_answers", ["account_id", "question_id"], [account_id, id])
        if response[1]:
            response = await Database.delete("faq", ["id", "account_id"], [id, account_id])
        return response[1]

    @staticmethod
    async def get_questions(account_id: int):
        response = await Database.select("faq", ["id", "question"], ["account_id"], [account_id])
        if response[1]:
            return response[0]
        return None

    @staticmethod
    async def save_answer(id: int, account_id: int, question_id: int, answer: str):
        response = await Database.update("faq_answers", ["id", "account_id", "question_id", "answer"], [id, account_id, question_id, answer])
        return response[1]

    @staticmethod
    async def delete_answer(id: int, account_id: int, question_id: int):
        response = await Database.delete("faq_answers", ["id", "account_id", "question_id"], [id, account_id, question_id])
        return response[1]

    @staticmethod
    async def get_answers(account_id: int, question_id: int):
        response = await Database.select("faq_answers", ["id", "answer"], ["account_id", "question_id"], [account_id, question_id])
        if response[1]:
            return response[0]
        return None

    @staticmethod
    async def get_all_answers(account_id: int):
        response = await Database.select("faq_answers", ["id", "question_id", "answer"], ["account_id"], [account_id])
        if response[1]:
            return response[0]
        return None

    @staticmethod
    async def save_command(id: int, account_id: int, command: str):
        response = await Database.update("commands", ["id", "account_id", "command"], [id, account_id, command])
        return response[1]

    @staticmethod
    async def delete_command(id: int, account_id: int):
        response = await Database.delete("aliases", ["account_id", "command_id"], [account_id, id])
        if response[1]:
            response = await Database.delete("responses", ["account_id", "command_id"], [account_id, id])
        if response[1]:
            response = await Database.delete("commands", ["id", "account_id"], [id, account_id])
        return response[1]

    @staticmethod
    async def get_commands(account_id: int):
        response = await Database.select("commands", ["id", "command"], ["account_id"], [account_id])
        if response[1]:
            return response[0]
        return None

    @staticmethod
    async def save_response(id: int, account_id: int, question_id: str, response: str):
        response = await Database.update("responses", ["id", "account_id", "command_id", "response"], [id, account_id, question_id, response])
        return response[1]

    @staticmethod
    async def delete_response(id: int, account_id: int, command_id: int):
        response = await Database.delete("responses", ["id", "account_id", "command_id"], [id, account_id, command_id])
        return response[1]

    @staticmethod
    async def get_responses(account_id: int, command_id: int):
        response = await Database.select("responses", ["id", "response"], ["account_id", "command_id"], [account_id, command_id])
        if response[1]:
            return response[0]
        return None

    async def get_all_responses(account_id: int):
        response = await Database.select("responses", ["id", "command_id", "response"], ["account_id"], [account_id])
        if response[1]:
            return response[0]
        return None

    @staticmethod
    async def save_alias(id: int, account_id: int, command_id: int, alias: str):
        response = await Database.update("aliases", ["id", "account_id", "command_id", "alias"], [id, account_id, command_id, alias])
        return response[1]

    @staticmethod
    async def delete_alias(id: int, account_id: int, command_id: int):
        response = await Database.delete("aliases", ["id", "account_id", "command_id"], [id, account_id, command_id])
        return response[1]

    @staticmethod
    async def get_aliases(account_id: int, command_id: int):
        response = await Database.select("aliases", ["id", "alias"], ["account_id", "command_id"], [account_id, command_id])
        if response[1]:
            return response[0]
        return None

    @staticmethod
    async def get_all_aliases(account_id: int):
        response = await Database.select("aliases", ["id", "command_id", "alias"], ["account_id"], [account_id])
        if response[1]:
            return response[0]
        return None
    
    @staticmethod
    async def get_chat_log(id):
        response = await Database.select("chat_logs", ["user", "message", "time"], ["account_id"], [id])
        if response[1]:
            if not response[0]:
                return []
            return response[0]
        return []

    @staticmethod
    async def has_admin_rights(role_id):
        response = await Database.select("roles", ["admin"], ["id"], [role_id])
        if response[1] and len(response[0]) > 0:
            return response[0][0]["admin"] == 1
        return False