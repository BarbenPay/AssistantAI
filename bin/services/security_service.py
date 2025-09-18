# services/security_service.py

import requests
import config
import time
import hashlib

def _get_analysis_report(analysis_id, headers):
    """Interroge le rapport d'analyse jusqu'à ce qu'il soit complété."""
    url_analysis = f"https://www.virustotal.com/api/v3/analyses/{analysis_id}"
    for _ in range(12):  # On essaie pendant 2 minutes (12 * 10s)
        response_analysis = requests.get(url_analysis, headers=headers, timeout=30)
        response_analysis.raise_for_status()
        result = response_analysis.json()
        if result["data"]["attributes"]["status"] == "completed":
            return result
        time.sleep(10)
    print("      -> L'analyse VirusTotal a pris trop de temps. Le fichier est considéré comme non sûr par précaution.")
    return None

def scan_file_with_virustotal(file_data: bytes):
    """
    Envoie des données de fichier à l'API VirusTotal pour analyse et renvoie si le fichier est sûr.
    Gère les fichiers déjà soumis.
    """
    if not config.VIRUSTOTAL_API_KEY:
        print("      -> AVERTISSEMENT : Clé API VirusTotal non configurée. Le scan de sécurité est ignoré.")
        return True

    print("      -> Contact de l'API VirusTotal pour analyse de sécurité...")
    headers = {"x-apikey": config.VIRUSTOTAL_API_KEY}
    
    # On calcule le hash pour identifier le fichier
    file_hash = hashlib.sha256(file_data).hexdigest()
    url_check_report = f"https://www.virustotal.com/api/v3/files/{file_hash}"

    try:
        # 1. Vérifier si un rapport existe déjà
        response_check = requests.get(url_check_report, headers=headers, timeout=30)
        
        analysis_result = None
        
        if response_check.status_code == 200:
            print("      -> Un rapport existant a été trouvé pour ce fichier.")
            # Si le rapport existe, on récupère directement l'ID de la dernière analyse
            analysis_id = response_check.json()["data"]["attributes"]["last_analysis_results"]
            # On doit reconstruire un semblant de rapport pour la suite
            stats = response_check.json()["data"]["attributes"]["last_analysis_stats"]
            analysis_result = {"data": {"attributes": {"stats": stats}}}

        elif response_check.status_code == 404:
            print("      -> Aucun rapport existant. Envoi du fichier pour une nouvelle analyse.")
            # 2. Si le fichier est inconnu, on l'envoie
            url_upload = "https://www.virustotal.com/api/v3/files"
            files = {"file": (file_hash, file_data)}
            response_upload = requests.post(url_upload, headers=headers, files=files, timeout=60)
            response_upload.raise_for_status()
            analysis_id = response_upload.json()["data"]["id"]
            analysis_result = _get_analysis_report(analysis_id, headers)
        
        else:
            # Gérer d'autres erreurs HTTP inattendues
            response_check.raise_for_status()

        if not analysis_result:
            return False # L'analyse a échoué ou a pris trop de temps

        # 3. Vérifier les résultats
        stats = analysis_result["data"]["attributes"]["stats"]
        malicious_votes = stats.get("malicious", 0) + stats.get("suspicious", 0)
        
        print(f"      -> Rapport VirusTotal : {malicious_votes} détection(s) malveillante(s) ou suspecte(s).")

        return malicious_votes == 0

    except requests.exceptions.RequestException as e:
        print(f"      -> Erreur de communication avec l'API VirusTotal : {e}")
        return False
