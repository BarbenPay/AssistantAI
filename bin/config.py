# config.py

import os
from dotenv import load_dotenv

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

dotenv_path = os.path.join(PROJECT_ROOT, 'config', '.env')
load_dotenv(dotenv_path=dotenv_path)

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

MODEL_PATH = os.path.join(PROJECT_ROOT, 'model', 'mistral-7b-instruct-v0.2.Q4_K_M.gguf')
N_CTX = 4096

CREDENTIALS_PATH = os.path.join(PROJECT_ROOT, 'config', 'credentials.json')
TOKEN_PATH = os.path.join(PROJECT_ROOT, 'token.json')

DB_PATH = os.path.join(PROJECT_ROOT, 'tasks.db')

VIRUSTOTAL_API_KEY = os.getenv("VIRUSTOTAL_API_KEY")