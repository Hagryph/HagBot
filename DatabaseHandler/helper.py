from datetime import datetime
from asyncpg import Record

def is_iso_format(date_string):
    try:
        datetime.fromisoformat(date_string)
        return True
    except:
        return False

def convert_iso_format_to_datetime(data):
    if isinstance(data, list):
        return [convert_iso_format_to_datetime(element) for element in data]
    elif isinstance(data, dict):
        return {key: convert_iso_format_to_datetime(value) for key, value in data.items()}
    elif isinstance(data, str) and is_iso_format(data):
        return datetime.fromisoformat(data)
    return data

def make_serializable(data):
    if isinstance(data, list):
        return [make_serializable(element) for element in data]
    elif isinstance(data, dict):
        return {key: make_serializable(value) for key, value in data.items()}
    elif isinstance(data, tuple):
        return tuple(make_serializable(element) for element in data)
    elif isinstance(data, Record):
        return {key: make_serializable(value) for key, value in data.items()}
    elif isinstance(data, datetime):
        return data.isoformat()
    return data