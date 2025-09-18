# services/mistral_service.py

from llama_cpp import Llama
import config
import json
import re

# Charger le modèle une seule fois au démarrage.
# Assurez-vous que le chemin dans config.py est correct.
llm = Llama(
    model_path=config.MODEL_PATH,
    n_gpu_layers=-1, # Mettre -1 pour utiliser le GPU, 0 pour le CPU
    n_ctx=4096, # Contexte du modèle
    n_batch=512,
    flash_attn=True,
    verbose=False      
)

def call_mistral(prompt: str, max_token = 500) -> str:
    """
    Fonction générique pour appeler le modèle Mistral local.
    Prend un prompt en entrée et retourne la réponse textuelle brute.
    """
    try:
        output = llm(
            prompt,
            max_tokens=max_token,
            stop=["[INST]", "USER:"], # Arrête la génération à ces mots
            echo=False
        )
        response_text = output["choices"][0]["text"].strip()
        return response_text
    except Exception as e:
        print(f"Erreur lors de l'appel au modèle Mistral : {e}")
        return "" # Retourne une chaîne vide en cas d'erreur

def get_json_from_mistral(prompt: str) -> dict:
    """
    Appelle Mistral, attend une réponse contenant du JSON, l'extrait et la parse.
    Retourne un dictionnaire Python.
    """
    raw_text = call_mistral(prompt)
    if not raw_text:
        return None

    # Regex pour trouver un bloc de code JSON, similaire à celle pour Gemini
    match = re.search(r'```json\s*(\{.*?\})\s*```', raw_text, re.DOTALL)
    if not match:
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