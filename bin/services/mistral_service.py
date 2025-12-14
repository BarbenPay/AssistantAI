# services/mistral_service.py

from llama_cpp import Llama
import config
import json
import re


llm = Llama(
    model_path=config.MODEL_PATH,
    n_gpu_layers=-1,
    n_ctx=4096,
    n_batch=512,
    flash_attn=True,
    verbose=True
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
            stop=["[INST]", "USER:"],
            echo=False
        )
        response_text = output["choices"][0]["text"].strip()
        return response_text
    except Exception as e:
        print(f"Erreur lors de l'appel au modèle Mistral : {e}")
        return ""

def get_json_from_mistral(prompt: str) -> dict:
    """
    Appelle Mistral, attend une réponse contenant du JSON, l'extrait et la parse.
    Retourne un dictionnaire Python.
    """
    raw_text = call_mistral(prompt)
    if not raw_text:
        return None

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