import os
import random

def get_openai_api_key():
    keys = [
        os.getenv("OPENAI_API_KEY_1"),
        os.getenv("OPENAI_API_KEY_2"),
        os.getenv("OPENAI_API_KEY_3"),
        os.getenv("OPENAI_API_KEY_4"),
        os.getenv("OPENAI_API_KEY_5"),
        os.getenv("OPENAI_API_KEY_6"),
        os.getenv("OPENAI_API_KEY_7"),
        os.getenv("OPENAI_API_KEY_8"),
        os.getenv("OPENAI_API_KEY_9"),
        os.getenv("OPENAI_API_KEY_10")
    ]
    return random.choice([k for k in keys if k])

