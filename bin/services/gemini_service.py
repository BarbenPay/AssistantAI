# gemini_service.py

import google.generativeai as genai
import config  # On importe notre nouvelle configuration !
import json
import re

# S'assurer que la clé API est disponible
if not config.GEMINI_API_KEY:
    raise ValueError("La clé API Gemini n'est pas définie. Vérifiez votre fichier .env.")

# Configuration de l'API avec la clé du fichier de config
genai.configure(api_key=config.GEMINI_API_KEY)

# Création d'un modèle réutilisable pour ne pas le recréer à chaque appel
model = genai.GenerativeModel('gemini-2.5-flash')

def call_gemini(prompt: str) -> str:
    """
    Fonction générique pour appeler l'API Gemini.
    Prend un prompt en entrée et retourne la réponse textuelle brute.
    """
    try:
        response = model.generate_content(prompt)
        # Gestion des cas où la réponse pourrait être bloquée
        if not response.parts:
            return "La réponse a été bloquée par les filtres de sécurité."
        return response.text
    except Exception as e:
        print(f"Erreur lors de l'appel à l'API Gemini : {e}")
        return "" # Retourne une chaîne vide en cas d'erreur

def get_json_from_gemini(prompt: str) -> dict:
    """
    Appelle Gemini, attend une réponse contenant du JSON, l'extrait et la parse.
    Retourne un dictionnaire Python.
    """
    raw_text = call_gemini(prompt)
    if not raw_text:
        return None

    # Regex améliorée pour trouver un bloc de code JSON
    match = re.search(r'```json\s*(\{.*?\})\s*```', raw_text, re.DOTALL)
    if not match:
        # Si le premier format n'est pas trouvé, on cherche un JSON simple
        match = re.search(r'(\{.*?\})', raw_text, re.DOTALL)

    if match:
        json_str = match.group(1)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"Erreur: Impossible de parser le JSON fourni par l'IA. Erreur: {e}")
            print(f"Réponse reçue:\n{json_str}")
            return None

    print("Aucun objet JSON n'a été trouvé dans la réponse.")
    return None