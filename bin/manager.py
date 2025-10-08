# manager.py

import config
from agents import email_agent, agenda_agent, task_agent
from datetime import datetime, timedelta
from services.mistral_service import get_json_from_mistral, call_mistral

# --- Mémoire interne de l'assistant (inchangée) ---
internal_memory = []

def clear_internal_memory():
    global internal_memory
    internal_memory = []

# --- Fonctions de formatage pour la GUI ---
def format_tasks_as_string(tasks):
    if not tasks:
        return "Aucune tâche à afficher."
    response = "Voici vos tâches :\n"
    for task in tasks:
        priority_map = {1: "Haute", 2: "Moyenne", 3: "Basse"}
        due_date_str = "N/A"
        if task.get('due_date'):
            try:
                due_date_str = datetime.strptime(task['due_date'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
            except (ValueError, TypeError):
                due_date_str = "Date invalide"
        response += f"- [ID: {task['id']}] {task['description']} (Priorité: {priority_map.get(task['priority'], 'N/A')}, Statut: {task['status']}, Échéance: {due_date_str})\n"
    return response.strip()

def format_events_as_string(events):
    if not events:
        return "Aucun événement à venir dans votre agenda."
    if isinstance(events, str):
        return events
    response = "Voici vos 10 prochains événements :\n"
    for event in events:
        summary = event.get('summary', 'Sans titre')
        start_raw  = event.get('start', '')
        try:
            # Tente de parser une date/heure complète (avec fuseau horaire)
            dt_object = datetime.fromisoformat(start_raw.replace('Z', '+00:00'))
            # Formate en "Jour mois année à HH:MM"
            start_formatted = dt_object.strftime('%d %B %Y à %H:%M')
        except (ValueError, TypeError):
            # Si ce n'est pas une date/heure complète, c'est probablement une date (AAAA-MM-JJ)
            try:
                dt_object = datetime.strptime(start_raw, '%Y-%m-%d')
                # Formate en "Jour mois année"
                start_formatted = dt_object.strftime('%d %B %Y') + " (toute la journée)"
            except (ValueError, TypeError):
                # Si le formatage échoue, on affiche la date brute
                start_formatted = start_raw

        response += f"- {summary} (Le {start_formatted})\n"

    return response

def format_emails_as_string(analyzed_emails):
    if not analyzed_emails:
        return "Aucun e-mail à analyser ou une erreur est survenue."
    response = "Analyse des e-mails terminée :\n"
    for i, analysis in enumerate(analyzed_emails):
        response += f"--- Email {i+1} ---\n"
        response += f"  Résumé: {analysis.get('resume', 'N/A')}\n"
        response += f"  Importance: {analysis.get('importance', 'N/A')}/5\n"
        response += f"  Action suggérée: {analysis.get('action_requise', 'N/A')}\n"
    return response.strip()

def parse_user_intent(user_query):
    # ... (cette fonction reste inchangée)
    today_date = datetime.now().strftime("%Y-%m-%d")
    prompt = f"""
[INST]
Tu es un expert en traitement du langage. Ta mission est de décomposer la demande de l'utilisateur en une intention et des entités précises.
Réponds UNIQUEMENT avec un objet JSON.

### Intentions possibles
"get_emails", "get_agenda", "add_event", "delete_event", 
"add_task", "get_tasks", "update_task_status", "delete_task", 
"get_general_recommendation", "get_urgent_recommendation", "unknown".

### Entités à extraire
- "summary": Le titre ou la description.
- "date": La date d'un événement ou l'échéance d'une tâche (format AAAA-MM-DD).
- "priority": La priorité d'une tâche (1 pour 'urgent', 2 pour 'moyen', 3 pour 'normal'). Par défaut 3.
- "status": Le statut d'une tâche ('à faire', 'en cours', 'terminé').

### EXEMPLES ###
Demande: "analyse mes emails" -> {{"intent": "get_emails"}}
Demande: "montre-moi mon agenda" -> {{"intent": "get_agenda"}}
Demande: "ajoute 'Rdv docteur' le 25 décembre" -> {{"intent": "add_event", "summary": "Rdv docteur", "date": "{datetime.now().year}-12-25"}}
Demande: "supprime l'événement 'réunion projet'" -> {{"intent": "delete_event", "summary": "réunion projet"}}
Demande: "ajoute la tâche urgente 'Finir le rapport' pour demain" -> {{"intent": "add_task", "summary": "Finir le rapport", "priority": 1, "date": "{(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')}"}}
Demande: "montre-moi les tâches terminées" -> {{"intent": "get_tasks", "status": "terminé"}}
Demande: "passe la tâche 'répondre à l'email' au statut en cours" -> {{"intent": "update_task_status", "summary": "répondre à l'email", "status": "en cours"}}
Demande: "donne-moi une recommandation" -> {{"intent": "get_general_recommendation"}}
Demande: "qu'est ce que j'ai d'urgent à faire aujourd'hui" -> {{"intent": "get_urgent_recommendation"}}

### DEMANDE À ANALYSER ###
Date actuelle: {today_date}
Demande: "{user_query}"
Réponse JSON:
[/INST]
"""
    return get_json_from_mistral(prompt) or {"intent": "unknown"}

# --- NOUVELLE FONCTION PRINCIPALE ---
def process_user_query(user_query: str) -> str:
    """
    Prend une requête utilisateur, la traite et retourne une réponse textuelle.
    """
    parsed_command = parse_user_intent(user_query)
    intent = parsed_command.get("intent")

    if intent == "add_task":
        summary = parsed_command.get("summary")
        if summary:
            priority = parsed_command.get("priority", 3)
            due_date = parsed_command.get("date")
            due_date_full = f"{due_date} 23:59:59" if due_date else None
            task_agent.add_task(description=summary, priority=priority, due_date=due_date_full)
            return f"Tâche '{summary}' ajoutée avec succès."
        else:
            return "Je n'ai pas compris quelle tâche ajouter."

    elif intent == "get_tasks":
        status_filter = parsed_command.get("status")
        tasks = []
        if status_filter:
            tasks = task_agent.get_tasks(status_filter=status_filter)
        else:
            tasks = task_agent.get_tasks(status_filter=['à faire', 'en cours'])
        return format_tasks_as_string(tasks)

    elif intent == "get_emails":
        analyzed_emails = email_agent.get_email_analysis()
        return format_emails_as_string(analyzed_emails)

    elif intent == "get_agenda":
        upcoming_events = agenda_agent.get_upcoming_events()
        return format_events_as_string(upcoming_events)

    elif intent == "add_event":
        summary = parsed_command.get("summary")
        date = parsed_command.get("date")
        if summary and date:
            agenda_agent.add_event(summary, date)
            return f"Événement '{summary}' ajouté pour le {date}."
        else:
            return "Il me manque des informations (nom et date de l'événement)."

    # Ajoutez ici les autres 'elif' pour les autres intents...
    # Pour l'instant, on met une réponse par défaut pour les autres cas.

    else:
        # Pour les intents plus complexes ou non listés, on peut appeler le LLM
        prompt = f"[INST]Réponds de manière concise à la question suivante : {user_query}[/INST]"
        response = call_mistral(prompt)
        return response if response else "Désolé, je ne suis pas sûr de comprendre. Pouvez-vous reformuler ?"


# --- Boucle principale pour le mode console (ne sera pas utilisée par la GUI) ---
def main_console():
    print("="*50)
    print("🤖 Assistant Manager Opérationnel. Tapez 'quitter' pour arrêter.")
    print("="*50)

    while True:
        user_input = input("\n> ")
        if user_input.lower() == 'quitter':
            print("Au revoir !")
            break

        # On utilise notre nouvelle fonction et on affiche le résultat
        response = process_user_query(user_input)
        print(f"\nAssistant: {response}")

if __name__ == "__main__":
    task_agent.setup_database()
    main_console()