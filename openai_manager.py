import os
import openai

def get_available_api_key():
    api_keys = os.getenv("OPENAI_API_KEYS").split(",")
    for key in api_keys:
        openai.api_key = key
        try:
            openai.Model.list()
            return key
        except openai.error.RateLimitError:
            continue
    return None

