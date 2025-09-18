# agents/email_agent.py

import email
from email.header import decode_header
import imaplib
from bs4 import BeautifulSoup
import fitz
import config
from services.mistral_service import get_json_from_mistral, call_mistral, llm
from services.security_service import scan_file_with_virustotal

CHUNK_SIZE = 3000 

def get_emails(max_count=5):
    """
    Se connecte à la boîte mail et récupère les 'max_count' derniers e-mails.
    """
    try:
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        mail.login(config.EMAIL_ADDRESS, config.EMAIL_PASSWORD)
        mail.select('inbox')
        status, data = mail.search(None, 'ALL')
        
        if status != 'OK':
            return []

        mail_ids = data[0].split()
        latest_mail_ids = mail_ids[-max_count:]
        emails = []

        for mail_id in reversed(latest_mail_ids):
            status, data = mail.fetch(mail_id, '(RFC822)')
            if status == 'OK':
                emails.append(data[0][1])
        
        mail.logout()
        return emails
        
    except Exception as e:
        print(f"Erreur lors de la récupération des e-mails: {e}")
        return []

def parse_email(raw_email):
    """
    Parse un e-mail brut pour extraire l'expéditeur, le sujet, le corps et le contenu des PDF analysés comme sûrs.
    """
    msg = email.message_from_bytes(raw_email)
    
    sender, encoding = decode_header(msg.get('From'))[0]
    if isinstance(sender, bytes):
        sender = sender.decode(encoding if encoding else 'utf-8')
    sender_email = email.utils.parseaddr(sender)[1]

    subject, encoding = decode_header(msg['Subject'])[0]
    if isinstance(subject, bytes):
        subject = subject.decode(encoding if encoding else 'utf-8')

    body = ""
    pdf_text = ""

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            if "attachment" not in content_disposition:
                if content_type == "text/plain" and not body:
                    try: body = part.get_payload(decode=True).decode()
                    except: continue
                elif content_type == "text/html":
                    try:
                        html_body = part.get_payload(decode=True).decode()
                        if not body: body = BeautifulSoup(html_body, "html.parser").get_text()
                    except: continue
            
            elif "attachment" in content_disposition and part.get_filename() and part.get_filename().lower().endswith('.pdf'):
                filename = part.get_filename()
                print(f"      -> Pièce jointe PDF trouvée: {filename}")
                pdf_data = part.get_payload(decode=True)
                
                is_safe = scan_file_with_virustotal(pdf_data)
                
                if is_safe:
                    print(f"      -> Le fichier '{filename}' est sûr. Lecture du contenu.")
                    try:
                        with fitz.open(stream=pdf_data, filetype="pdf") as doc:
                            for page in doc:
                                pdf_text += page.get_text() + "\n"
                    except Exception as e:
                        print(f"      -> Erreur lors de la lecture du PDF pourtant jugé sûr : {e}")
                else:
                    print(f"      -> ATTENTION : Le fichier '{filename}' a été jugé non sûr et sera ignoré.")
                    pdf_text += f"\n\n--- PIECE JOINTE '{filename}' IGNORÉE CAR POTENTIELLEMENT DANGEREUSE ---\n"

    else:
        try: body = msg.get_payload(decode=True).decode()
        except: body = "Corps de l'e-mail illisible."
    
    full_body = f"{body}\n\n{pdf_text}"
    return sender_email, subject, full_body.strip()

def _summarize_long_body(body_text):
    print("      -> Le corps de l'e-mail est très long, résumé par morceaux en cours...")
    tokens = llm.tokenize(body_text.encode('utf-8', errors='ignore'))
    chunks = [llm.detokenize(tokens[i:i + CHUNK_SIZE]).decode('utf-8', errors='ignore') for i in range(0, len(tokens), CHUNK_SIZE)]
    summaries = []
    for i, chunk in enumerate(chunks):
        print(f"      -> Résumé du morceau {i+1}/{len(chunks)}...")
        prompt = f"[INST]Résume le morceau de texte suivant de manière concise:\n\n{chunk}[/INST]"
        summary = call_mistral(prompt)
        if summary: summaries.append(summary)
    print("      -> Combinaison des résumés...")
    combined_summary = "\n\n".join(summaries)
    final_prompt = f"[INST]Combine les résumés partiels suivants en un seul résumé global et cohérent:\n\n{combined_summary}[/INST]"
    return call_mistral(final_prompt) or "Résumé impossible à générer."

def analyze_email_with_llm(sender, subject, body):
    analysis_prompt = f"""
[INST]
Tu es un assistant IA expert qui analyse des e-mails. Ta tâche est de lire un e-mail (expéditeur, sujet et corps) et de renvoyer une analyse au format JSON. L'expéditeur est un indice crucial pour déterminer l'importance.

### EXEMPLE PARFAIT ###
Expéditeur: notifications@github.com
Sujet: [CodeReader] New issue: "Bug in UI"
Corps: A new issue has been created in your repository...

Réponse attendue:
```json
{{
  "resume": "Un nouveau ticket (bug UI) a été ouvert sur le dépôt CodeReader de GitHub.",
  "importance": 4,
  "action_requise": "Consulter"
}}
```

### E-MAIL À ANALYSER ###
Expéditeur: {sender}
Sujet: {subject}
Corps: {body}

Réponse attendue:
[/INST]
"""
    prompt_tokens = llm.tokenize(analysis_prompt.encode('utf-8', errors='ignore'))
    if len(prompt_tokens) > (config.N_CTX - 500):
        body = _summarize_long_body(body)
        analysis_prompt = f"""
[INST]
Tu es un assistant IA expert qui analyse des e-mails. Ta tâche est de lire un e-mail (expéditeur, sujet et corps) et de renvoyer une analyse au format JSON. L'expéditeur est un indice crucial pour déterminer l'importance.

### EXEMPLE PARFAIT ###
Expéditeur: notifications@github.com
Sujet: [CodeReader] New issue: "Bug in UI"
Corps: A new issue has been created in your repository...

Réponse attendue:
```json
{{
  "resume": "Un nouveau ticket (bug UI) a été ouvert sur le dépôt CodeReader de GitHub.",
  "importance": 4,
  "action_requise": "Consulter"
}}
```

### E-MAIL À ANALYSER ###
Expéditeur: {sender}
Sujet: {subject}
Corps: {body}

Réponse attendue:
[/INST]
"""
    return get_json_from_mistral(analysis_prompt)

def get_email_analysis(max_count=5):
    print(f"Agent E-mail: Récupération des {max_count} derniers e-mails...")
    raw_emails = get_emails(max_count)
    if not raw_emails:
        print("Agent E-mail: Aucun e-mail trouvé ou erreur de connexion.")
        return []
    print(f"Agent E-mail: {len(raw_emails)} e-mail(s) trouvé(s). Analyse en cours...")
    all_analyses = []
    for raw_email in raw_emails:
        # --- CORRECTION ICI ---
        # On récupère bien les 3 valeurs (sender, subject, body)
        sender, subject, body = parse_email(raw_email)
        print(f"Agent E-mail: Analyse de '{subject}' de '{sender}'...")
        try:
            analysis = analyze_email_with_llm(sender, subject, body)
            if analysis:
                analysis['subject'] = subject
                all_analyses.append(analysis)
            else:
                print(f"      -> Échec de l'analyse pour '{subject}'. Aucune réponse JSON valide reçue.")
        except Exception as e:
            print(f"      -> Une erreur inattendue est survenue lors de l'analyse de '{subject}': {e}")
    return all_analyses
