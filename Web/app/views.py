from django.shortcuts import redirect, render
from django.http.request import HttpRequest
from django.http import HttpResponseServerError, HttpResponse
from backend.twitch import OAuth
from backend.account import Account
from backend.database import Database
from hag_logger import Logger
from input_sanitizer import sanitizers
import json

users = {}
_logger = Logger("app_error.txt")

def index(request: HttpRequest):
    return render(request, "index.html")

def login(request: HttpRequest):
    return redirect(OAuth.get_login_url())

async def logout(request: HttpRequest):
    response = redirect("/")
    
    try:
        session_key = request.COOKIES.get("session_key")
        if session_key is not None:
            account_id = await Database.get_id_from_session_key(session_key)
            if account_id is not None:
                account = users[account_id]
                await account.delete_session()
        response.delete_cookie("session_key")
    except:
        pass

    return response

async def redirect_url(request: HttpRequest):
    try:
        code = request.GET.get("code")
        if code is None:
            return redirect("/denied")
        (
            access_token,
            refresh_token,
            user_id,
            user_name,
            user_avatar_path,
        ) = OAuth.get_access_token(code)
        if user_id in users:
            account = users[user_id]
            if account:
                response = redirect("/dashboard")
                response = await account.login(user_name, access_token, refresh_token, user_avatar_path, response)
                return response
            else:
                return HttpResponseServerError("500 Internal Server Error")
        else:
            account = Account(user_id)
            response = redirect("/dashboard")
            response = await account.login(
                user_name, access_token, refresh_token, user_avatar_path, response
            )
            users[user_id] = (account)
            return response
    except Exception as e:
        _logger.log(f"An error occurred while logging in: {e}")
        return HttpResponseServerError("500 Internal Server Error")

async def faq_form(request: HttpRequest, account: Account):
    await account.save_config("faq_enabled", (int)(request.POST.get("enabled") != None))
    questions = [question.get("id") for question in await account.get_questions()]
    new_questions = []
    answers = [(answer.get("id"), answer.get("question_id")) for answer in await account.get_all_answers()]
    new_answers = []

    for key, value in request.POST.items():
        if key.startswith("question-") and not key.endswith("save"):
            question_id = (int)(key.replace("question-", ""))
            cleaned_value = sanitizers.sanitize_data(value, bleach_kwargs={})
            new_questions.append(question_id)
            await account.save_question(question_id, cleaned_value)
        elif key.startswith("answer-"):
            question_id = (int)(key.split("-")[1])
            answer_id = (int)(key.split("-")[2])
            cleaned_value = sanitizers.sanitize_data(value, bleach_kwargs={})
            new_answers.append((answer_id, question_id))
            await account.save_answer(answer_id, question_id, cleaned_value)
    for question_id in questions:
        if question_id not in new_questions:
            await account.delete_question(question_id)
    for answer_id, question_id in answers:
        if (answer_id, question_id) not in new_answers:
            await account.delete_answer(answer_id, question_id)

async def commands_form(request: HttpRequest, account: Account):
    await account.save_config("custom_commands_enabled", (int)(request.POST.get("enabled") != None))
    commands = [command.get("id") for command in await account.get_commands()]
    new_commands = []
    responses = [(response.get("id"), response.get("command_id")) for response in await account.get_all_responses()]
    new_responses = []
    aliases = [(alias.get("id"), alias.get("command_id")) for alias in await account.get_all_aliases()]
    new_aliases = []

    for key, value in request.POST.items():
        if key.startswith("command-") and not key.endswith("save"):
            command_id = (int)(key.replace("command-", ""))
            cleaned_value = sanitizers.sanitize_data(value, bleach_kwargs={})
            new_commands.append(command_id)
            await account.save_command(command_id, cleaned_value)
        elif key.startswith("response-"):
            command_id = (int)(key.split("-")[1])
            response_id = (int)(key.split("-")[2])
            cleaned_value = sanitizers.sanitize_data(value, bleach_kwargs={})
            new_responses.append((response_id, command_id))
            await account.save_response(response_id, command_id, cleaned_value)
        elif key.startswith("alias-"):
            command_id = (int)(key.split("-")[1])
            alias_id = (int)(key.split("-")[2])
            cleaned_value = sanitizers.sanitize_data(value, bleach_kwargs={})
            new_aliases.append((alias_id, command_id))
            await account.save_alias(alias_id, command_id, cleaned_value)
    for command_id in commands:
        if command_id not in new_commands:
            await account.delete_command(command_id)
    for response_id, command_id in responses:
        if (response_id, command_id) not in new_responses:
            await account.delete_response(response_id, command_id)
    for alias_id, command_id in aliases:
        if (alias_id, command_id) not in new_aliases:
                await account.delete_alias(alias_id, command_id)
    
async def dashboard(request: HttpRequest):
    session_key = request.COOKIES.get("session_key")
    account_id = await Database.get_id_from_session_key(session_key)
    account = users[account_id]
    
    if request.method == "POST":
        match request.POST.get("form-name"):
            case "question":
                await faq_form(request, account)
            case "command":
                await commands_form(request, account)
    
    username = await Database.get_data(session_key, "username")
    avatar_link = await Database.get_data(session_key, "user_avatar_path")
    error_message = None
    show_admin_area = await account.has_admin_rights()
    tables = []

    if show_admin_area:
        table_names, _ = await Database.tables()
        for table_name in table_names:
            columns, _ = await Database.columns(table_name)
            column_names = [column_name["column_name"] for column_name in columns]
            rows, _ = await Database.select(table_name, column_names)
            rows = [[row[column] for column in row] for row in rows]
            table = {"name": table_name, "columns": column_names, "rows": rows}
            tables.append(table)

    faq_enabled = await account.get_config("faq_enabled") or False
    custom_commands_enabled = await account.get_config("custom_commands_enabled") or False

    return render(
        request,
        "dashboard.html",
        {
            "username": username,
            "error_message": error_message,
            "show_admin_area": show_admin_area,
            "faq_enabled": faq_enabled,
            "custom_commands_enabled": custom_commands_enabled,
            "tables": tables,
            "avatar_link": avatar_link,
        },
    )

async def get_chat_log(request: HttpRequest):
    session_key = request.COOKIES.get("session_key")
    account_id = await Database.get_id_from_session_key(session_key)
    account = users[account_id]
    chat_log = await account.get_chat_log()
    return HttpResponse(json.dumps(chat_log), content_type="application/json")

async def get_questions(request: HttpRequest):
    session_key = request.COOKIES.get("session_key")
    account_id = await Database.get_id_from_session_key(session_key)
    account = users[account_id]
    questions = await account.get_questions()
    return HttpResponse(json.dumps(questions), content_type="application/json")

async def get_answers(request: HttpRequest):
    session_key = request.COOKIES.get("session_key")
    account_id = await Database.get_id_from_session_key(session_key)
    account = users[account_id]
    answers = await account.get_all_answers()
    return HttpResponse(json.dumps(answers), content_type="application/json")

async def get_commands(request: HttpRequest):
    session_key = request.COOKIES.get("session_key")
    account_id = await Database.get_id_from_session_key(session_key)
    account = users[account_id]
    commands = await account.get_commands()
    return HttpResponse(json.dumps(commands), content_type="application/json")

async def get_responses(request: HttpRequest):
    session_key = request.COOKIES.get("session_key")
    account_id = await Database.get_id_from_session_key(session_key)
    account = users[account_id]
    responses = await account.get_all_responses()
    return HttpResponse(json.dumps(responses), content_type="application/json")

async def get_aliases(request: HttpRequest):
    session_key = request.COOKIES.get("session_key")
    account_id = await Database.get_id_from_session_key(session_key)
    account = users[account_id]
    aliases = await account.get_all_aliases()
    return HttpResponse(json.dumps(aliases), content_type="application/json")

def denied(request: HttpRequest):
    return render(request, "denied_access.html")