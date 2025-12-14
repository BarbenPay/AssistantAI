# agents/task_agent.py

import sqlite3
import os
from datetime import datetime
import config



def setup_database():
    with sqlite3.connect(config.DB_PATH) as conn:
        
        
        """
        Initialise la base de données et la table 'tasks' avec une structure de données enrichie.
        Cette fonction remplace l'ancienne 'initialize_database'.
        """
        conn = sqlite3.connect(config.DB_PATH)
        c = conn.cursor()
        c.execute('DROP TABLE IF EXISTS tasks')
        c.execute('''
            CREATE TABLE tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'à faire', -- 'à faire', 'en cours', 'terminé'
                priority INTEGER DEFAULT 3, -- 1=Haute, 2=Moyenne, 3=Basse
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                due_date DATETIME, -- Date limite pour la tâche (optionnel)
                source TEXT DEFAULT 'manuel' -- D'où vient la tâche ? 'manuel', 'email_agent', etc.
            )
        ''')
        conn.commit()
        conn.close()
        print("[Task Agent] Base de données initialisée avec la nouvelle structure.")

def add_task(description, priority=3, due_date=None, source='manuel'):
    """
    Ajoute une nouvelle tâche avec des détails enrichis.
    """
    conn = sqlite3.connect(config.DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO tasks (description, priority, due_date, source) VALUES (?, ?, ?, ?)",
        (description, priority, due_date, source)
    )
    conn.commit()
    conn.close()
    print(f"[Task Agent] Tâche ajoutée : '{description}' (Priorité: {priority})")

def get_tasks(status_filter=None):
    """
    Récupère une liste de tâches, avec un filtre optionnel par statut.
    Retourne une liste de dictionnaires pour une utilisation facile.
    """
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    query = "SELECT * FROM tasks"
    params = []
    if status_filter:
        if isinstance(status_filter, list):
            placeholders = ','.join('?' for status in status_filter)
            query += f" WHERE status IN ({placeholders})"
            params.extend(status_filter)
        else:
            query += " WHERE status = ?"
            params.append(status_filter)
    
    query += " ORDER BY priority ASC, due_date ASC"

    c.execute(query, params)
    tasks = [dict(row) for row in c.fetchall()]
    conn.close()
    return tasks

def display_tasks(tasks):
    """Affiche joliment une liste de tâches."""
    if not tasks:
        print("Aucune tâche à afficher.")
        return
    
    for task in tasks:
        priority_map = {1: "Haute", 2: "Moyenne", 3: "Basse"}
        due_date_str = "N/A"
        if task.get('due_date'):
            try:
                due_date_str = datetime.strptime(task['due_date'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
            except (ValueError, TypeError):
                due_date_str = "Date invalide"
        print(
            f"- [ID: {task['id']}] {task['description']} "
            f"(Priorité: {priority_map.get(task['priority'], 'N/A')}, Statut: {task['status']}, "
            f"Échéance: {due_date_str})"
        )

def update_task_status(task_id, new_status):
    """
    Met à jour le statut d'une tâche (ex: 'à faire' -> 'en cours').
    Les statuts valides sont : 'à faire', 'en cours', 'terminé'.
    """
    if new_status not in ['à faire', 'en cours', 'terminé']:
        print(f"[Task Agent] Erreur : Statut '{new_status}' non valide.")
        return

    conn = sqlite3.connect(config.DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE tasks SET status = ? WHERE id = ?", (new_status, task_id))
    conn.commit()
    if c.rowcount > 0:
        print(f"[Task Agent] Le statut de la tâche {task_id} est maintenant '{new_status}'.")
    else:
        print(f"[Task Agent] Aucune tâche trouvée avec l'ID {task_id}.")
    conn.close()

def delete_task(task_id):
    """Supprime une tâche en utilisant son ID unique."""
    conn = sqlite3.connect(config.DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    if c.rowcount > 0:
        print(f"[Task Agent] La tâche {task_id} a été supprimée.")
    else:
        print(f"[Task Agent] Aucune tâche trouvée avec l'ID {task_id}.")
    conn.close()


if __name__ == '__main__':
    setup_database()

    print("\n--- Ajout de tâches de test ---")
    add_task("Répondre à l'email de Jean", priority=1, due_date="2025-07-10 18:00:00", source="email_agent")
    add_task("Préparer la présentation projet", priority=2)
    add_task("Faire les courses", priority=3)

    print("\n--- Affichage des tâches 'à faire' ---")
    open_tasks = get_tasks(status_filter='à faire')
    display_tasks(open_tasks)

    print("\n--- Mise à jour d'une tâche ---")
    if open_tasks:
        task_to_update_id = open_tasks[0]['id']
        update_task_status(task_to_update_id, 'terminé')

    print("\n--- Affichage de toutes les tâches ---")
    all_tasks = get_tasks()
    display_tasks(all_tasks)