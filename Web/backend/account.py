from hag_logger import Logger
from backend.database import Database
import asyncio

class Account:
    def __init__(self, id):
        self._logger = Logger("account_"  + str(id) + "_error.txt")
        self.id = id

    async def login(self, username, access_token, refresh_token, user_avatar_path, response):
        result = await Database.create_account(self.id, username, access_token, refresh_token)
        if not result:
            raise Exception(f"An error occured while creating/updating account with the ID {self.id}")
        result = await self.activate_account()
        if not result:
            raise Exception(f"An error occured while activating account with the ID {self.id}")
        return await self.create_session(response, username, user_avatar_path)

    async def activate_account(self):
        return await Database.activate_account(self.id)

    async def deactivate_account(self):
        return await Database.deactivate_account(self.id)

    async def is_active(self):
        return await Database.is_active(self.id)
        
    async def create_session(self, response, username, user_avatar_path):
        session_key = await Database.get_session(self.id)
        session_data = {"username": username, "user_avatar_path": user_avatar_path}
        if session_key is None or not all(await asyncio.gather(*[Database.get_data(session_key, key) for key in session_data])):
            response = await Database.create_session(self.id, response, session_data)
        else:
            response.set_cookie("session_key", session_key, httponly=True)
        return response

    async def delete_session(self):
        return await Database.delete_session(self.id)

    async def get_role(self):
        role = await Database.get_role(self.id)
        if role is not None:
            return role
        raise Exception(f"An error occurred while getting the role for ID {self.id}")

    async def get_username(self):
        username = await Database.get_username(self.id)
        if username:
            return username
        raise Exception(f"An error occurred while getting the username for ID {self.id}")
        
    async def save_config(self, column, value):
        return await Database.save_config(self.id, column, value)

    async def get_config(self, column):
        return await Database.get_config(self.id, column)

    async def get_access_token(self):
        return await Database.get_access_token(self.id)

    async def update_access_token(self, access_token):
        return await Database.update_access_token(self.id, access_token)

    async def get_refresh_token(self):
        return await Database.get_refresh_token(self.id)
    
    async def save_question(self, id: int, question: str):
        return await Database.save_question(id, self.id, question)

    async def delete_question(self, id: int):
        return await Database.delete_question(id, self.id)

    async def get_questions(self):
        return await Database.get_questions(self.id)
    
    async def save_answer(self, id: int, question_id: int, answer: str):
        return await Database.save_answer(id, self.id, question_id, answer)

    async def delete_answer(self, id: int, question_id: int):
        return await Database.delete_answer(id, self.id, question_id)
    
    async def get_answers(self, question_id: int):
        return await Database.get_answers(self.id, question_id)
    
    async def get_all_answers(self):
        return await Database.get_all_answers(self.id)
    
    async def save_command(self, id: int, command: str):
        return await Database.save_command(id, self.id, command)

    async def delete_command(self, id: int):
        return await Database.delete_command(id, self.id)

    async def get_commands(self):
        return await Database.get_commands(self.id)

    async def save_response(self, id: int, command_id: int, response: str):
        return await Database.save_response(id, self.id, command_id, response)

    async def delete_response(self, id: int, command_id: int):
        return await Database.delete_response(id, self.id, command_id)

    async def get_responses(self, command_id: int):
        return await Database.get_responses(self.id, command_id)

    async def get_all_responses(self):
        return await Database.get_all_responses(self.id)

    async def save_alias(self, id: int, command_id: int, alias: str):
        return await Database.save_alias(id, self.id, command_id, alias)

    async def delete_alias(self, id: int, command_id: int):
        return await Database.delete_alias(id, self.id, command_id)

    async def get_aliases(self, question_id: int):
        return await Database.get_aliases(self.id, question_id)

    async def get_all_aliases(self):
        return await Database.get_all_aliases(self.id)
    
    async def get_chat_log(self):
        return await Database.get_chat_log(self.id)

    async def has_admin_rights(self):
        return await Database.has_admin_rights(await self.get_role())