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

def parse_user_intent(user_query):
    """
    Analyse la demande de l'utilisateur pour en déduire l'intention et les entités.
    MISE À JOUR pour comprendre la priorité, les dates d'échéance et les statuts.
    """
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

def find_items_in_memory(summary_keyword):
    """Recherche dans la mémoire interne les éléments correspondant à un mot-clé."""
    return [item for item in internal_memory if summary_keyword.lower() in item['summary'].lower()]

def handle_item_selection(items):
    """Gère le cas où plusieurs éléments correspondent à la recherche."""
    if not items:
        print("Manager: Désolé, je n'ai trouvé aucun élément correspondant.")
        return None
    if len(items) == 1:
        return items[0]

    print("Manager: J'ai trouvé plusieurs éléments. Lequel vouliez-vous ?")
    for i, item in enumerate(items):
        source_label = "Tâche" if item['source'] == 'task' else "Agenda"
        # Utilise la fonction d'affichage de l'agent pour une présentation cohérente
        if item['source'] == 'task':
             print(f"  {i + 1}. [{source_label}] {item['summary']} (ID: {item['id']})")
        else:
             print(f"  {i + 1}. [{source_label}] {item['summary']}")

    while True:
        try:
            choice = int(input("Entrez le numéro de votre choix : "))
            if 1 <= choice <= len(items):
                return items[choice - 1]
            else:
                print("Numéro invalide. Veuillez réessayer.")
        except ValueError:
            print("Veuillez entrer un numéro.")

def populate_memory_with_tasks():
    """Charge les tâches ouvertes dans la mémoire interne en utilisant la nouvelle fonction get_tasks."""
    clear_internal_memory()
    # On récupère toutes les tâches non terminées pour la sélection
    tasks_a_faire = task_agent.get_tasks(status_filter='à faire')
    tasks_en_cours = task_agent.get_tasks(status_filter='en cours')
    
    # internal_memory devient une liste de dictionnaires
    for task in tasks_a_faire + tasks_en_cours:
        internal_memory.append({
            "id": task['id'],
            "summary": task['description'],
            "source": "task"
        })
        
def populate_memory_with_events():
    """Charge les événements à venir dans la mémoire interne."""
    clear_internal_memory()
    events = agenda_agent.get_upcoming_events(max_events=50) # Chercher plus loin
    for event in events:
        internal_memory.append({
            "id": event['id'],
            "summary": event['summary'],
            "source": "agenda"
        })

def get_general_recommendation():
    
    print("Manager: Je consulte mes agents pour vous suggérer sur quoi vous avancer...")
    raw_emails = email_agent.get_email_analysis()
    upcoming_events = agenda_agent.get_upcoming_events(max_events=10)

    prompt = """
[INST]
Tu es un assistant personnel expert. Analyse les informations ci-dessous pour créer un plan d'action priorisé des tâches importantes à venir.

### E-MAILS NON LUS ###
"""
    if raw_emails:
        for i, mail in enumerate(raw_emails):
            prompt += f"--- Email {i+1} ---\n"
            prompt += f"Sujet: {mail['subject']}\n"
            prompt += f"Corps: {mail['body'][:500]}...\n"
    else:
        prompt += "Aucun nouvel e-mail.\n"

    prompt += "\n### ÉVÉNEMENTS À VENIR ###\n"
    if upcoming_events:
        for event in upcoming_events:
            prompt += f"- {event['start']}: {event['summary']}\n"
    else:
        prompt += "Aucun événement à venir.\n"

    prompt += """
---
TÂCHE FINALE : En te basant sur TOUT ce qui précède, crée une liste de tâches, numérotée et ordonnée de la plus urgente à la moins importante. Ignore les publicités. Sois concis. Commence par "Pour vous avancer, voici vos prochaines actions prioritaires :".
[/INST]
"""
    
    print("Manager: Je réfléchis à vos priorités (1 seul appel API)...")
    recommendation = call_mistral(prompt) # On utilise notre service
    print("\n--- Plan d'Action Recommandé ---")
    print(recommendation)
    print("-" * 33)

def get_urgent_recommendation():

    print("Manager: Je consulte mes agents pour les urgences du jour...")
    raw_emails = email_agent.get_email_analysis()
    upcoming_events = agenda_agent.get_upcoming_events(max_events=10)
    today_str = datetime.now().strftime("%Y-%m-%d")

    prompt = f"""
[INST]
Tu es un assistant personnel expert. Analyse les informations ci-dessous pour identifier les tâches critiques à faire IMPÉRATIVEMENT aujourd'hui ({today_str}).

### E-MAILS IMPORTANTS NON LUS ###
"""
    if raw_emails:
        email_found = False
        for analysis in raw_emails:
             # Simulation d'une analyse rapide pour l'importance
            if "alerte" in analysis['subject'].lower() or "urgent" in analysis['subject'].lower():
                prompt += f"- Sujet: {analysis['subject']}\n"
                email_found = True
        if not email_found:
             prompt += "- Aucun e-mail urgent ne requiert votre attention immédiate.\n"
    else:
        prompt += "- Aucun e-mail important.\n"

    prompt += f"\n### ÉVÉNEMENTS DU JOUR ({today_str}) ###\n"
    event_found = False
    if upcoming_events:
        for event in upcoming_events:
            if today_str in event['start']:
                prompt += f"- {event['start']}: {event['summary']}\n"
                event_found = True
    if not event_found:
        prompt += "- Aucun événement prévu pour aujourd'hui.\n"

    prompt += """
---
TÂCHE FINALE : En te basant sur ces informations, liste les actions à faire aujourd'hui. Si rien n'est urgent, dis-le clairement. Commence par "Pour aujourd'hui, voici vos priorités :".
[/INST]
"""
    
    print("Manager: Je réfléchis à vos priorités (1 seul appel API)...")
    recommendation = call_mistral(prompt) # On utilise notre service
    print("\n--- Urgences du jour ---")
    print(recommendation)
    print("-" * 33)

def main():
    """Boucle principale de l'assistant manager."""
    print("="*50)
    print("🤖 Assistant Manager Opérationnel. Tapez 'quitter' pour arrêter.")
    print("="*50)

    while True:
        user_input = input("\n> ")
        if user_input.lower() == 'quitter':
            print("Au revoir !")
            break

        parsed_command = parse_user_intent(user_input)
        intent = parsed_command.get("intent")

         # --- GESTION DES TÂCHES (logique améliorée) ---
        if intent == "add_task":
            summary = parsed_command.get("summary")
            if summary:
                priority = parsed_command.get("priority", 3)
                due_date = parsed_command.get("date")
                due_date_full = f"{due_date} 23:59:59" if due_date else None
                task_agent.add_task(description=summary, priority=priority, due_date=due_date_full)
            else:
                print("Manager: Je n'ai pas compris quelle tâche ajouter.")

        elif intent == "get_tasks":
            status_filter = parsed_command.get("status")
            tasks = []
            if status_filter:
                print(f"Manager: Voici la liste de vos tâches '{status_filter}':")
                tasks = task_agent.get_tasks(status_filter=status_filter)
            else:
                print("Manager: Voici la liste de toutes vos tâches non terminées:")
                tasks = task_agent.get_tasks(status_filter=['à faire', 'en cours'])
            task_agent.display_tasks(tasks)

        elif intent == "update_task_status":
            new_status = parsed_command.get("status")
            if not new_status:
                print("Manager: Veuillez préciser le nouveau statut.")
                continue

            # 1. Montrer les tâches d'abord
            print("Manager: Quelle tâche voulez-vous mettre à jour ?")
            populate_memory_with_tasks() # Charge les tâches dans la mémoire
            
            # Utilise la mémoire qui est maintenant une liste de dicts
            all_tasks = [item for item in internal_memory if item['source'] == 'task']
            
            # 2. Utiliser handle_item_selection pour choisir
            selected_item = handle_item_selection(all_tasks)

            if selected_item:
                task_agent.update_task_status(selected_item['id'], new_status)

        elif intent == "delete_task":
            summary = parsed_command.get("summary")
            if not summary:
                print("Manager: Veuillez préciser quelle tâche supprimer.")
                continue
            populate_memory_with_tasks()
            selected_item = handle_item_selection(find_items_in_memory(summary))
            if selected_item:
                task_agent.delete_task(selected_item['id'])

        # --- GESTION EMAILS ET AGENDA (logique restaurée) ---
        elif intent == "get_emails":
            print("Manager: Compris. Je demande à l'agent e-mail de faire une analyse.")
            # Assurez-vous que cette fonction existe et affiche les résultats
            analyzed_emails = email_agent.get_email_analysis() 
            
            if not analyzed_emails:
                print("Aucun e-mail à analyser ou une erreur est survenue.")
            else:
                print("\n--- Analyse des E-mails ---")
                for i, analysis in enumerate(analyzed_emails):
                    print(f"Email {i+1}:")
                    print(f"  Résumé: {analysis.get('resume', 'N/A')}")
                    print(f"  Importance: {analysis.get('importance', 'N/A')}/5")
                    print(f"  Action suggérée: {analysis.get('action_requise', 'N/A')}")
                print("-" * 27)

        elif intent == "get_agenda":
            print("Manager: Compris. Je consulte l'agenda.")
            # Assurez-vous que cette fonction affiche les résultats
            upcoming_events = agenda_agent.get_upcoming_events() 
            
            if not upcoming_events:
                print("Aucun événement à venir dans votre agenda.")
            else:
                print("\n--- Vos 10 prochains événements ---")
                for event in upcoming_events:
                    start_time = event.get('start', 'N/A')
                    summary = event.get('summary', 'Sans titre')
                    print(f"- {start_time}: {summary}")
                print("-" * 33)

        elif intent == "add_event":
            summary = parsed_command.get("summary")
            date = parsed_command.get("date")
            if summary and date:
                print(f"Manager: J'ajoute '{summary}' pour le {date} à l'agenda.")
                agenda_agent.add_event(summary, date)
            else:
                print("Manager: Il me manque des informations (nom et date de l'événement).")

        elif intent == "delete_event":
            summary = parsed_command.get("summary")
            if not summary:
                print("Manager: Veuillez préciser le nom de l'événement à supprimer.")
                continue
            populate_memory_with_events()
            selected_item = handle_item_selection(find_items_in_memory(summary))
            if selected_item:
                # La suppression par nom est conservée ici, mais pourrait être remplacée par un delete_by_id si vous l'ajoutez à l'agent agenda.
                agenda_agent.delete_event(selected_item['summary']) 

        # --- RECOMMANDATIONS (logique restaurée) ---
        elif intent == "get_general_recommendation":
            print("Fonction de recommandation générale à implémenter.")
            get_general_recommendation()

        elif intent == "get_urgent_recommendation":
            print("Fonction de recommandation urgente à implémenter.")
            get_urgent_recommendation()

        else: # intent == "unknown"
            print("Manager: Désolé, je ne suis pas sûr de comprendre. Pouvez-vous reformuler ?")

if __name__ == "__main__":
    task_agent.setup_database()
    main()
