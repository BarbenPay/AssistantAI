# config.py

import os
from dotenv import load_dotenv

# Chemin vers le dossier du projet pour construire des chemins fiables
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Charger les variables d'environnement du fichier .env qui se trouve dans /config
# On construit le chemin complet pour être certain de le trouver
dotenv_path = os.path.join(PROJECT_ROOT, 'config', '.env')
load_dotenv(dotenv_path=dotenv_path)

# --- Clés API & Identifiants ---
# On charge toutes les variables ici, une bonne fois pour toutes.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

MODEL_PATH = os.path.join(PROJECT_ROOT, 'model', 'mistral-7b-instruct-v0.2.Q4_K_M.gguf')
N_CTX = 4096

# --- Chemins des Fichiers ---
CREDENTIALS_PATH = os.path.join(PROJECT_ROOT, 'config', 'credentials.json')
TOKEN_PATH = os.path.join(PROJECT_ROOT, 'token.json')

# --- Base de données ---
DB_PATH = os.path.join(PROJECT_ROOT, 'tasks.db')

VIRUSTOTAL_API_KEY = os.getenv("VIRUSTOTAL_API_KEY")