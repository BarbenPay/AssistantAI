import datetime
import os.path
import config
from google.auth import exceptions
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --- CONFIGURATION ---
SCOPES = ["https://www.googleapis.com/auth/calendar"]


def get_calendar_service():
    """Se connecte à l'API et retourne un objet 'service' pour interagir."""
    creds = None
    # Charger le token existant s'il est présent
    if os.path.exists(config.TOKEN_PATH):
        try:
            creds = Credentials.from_authorized_user_file(config.TOKEN_PATH, SCOPES)
        except Exception:
            # Token illisible/corrompu: on l'ignorera et on ré-authentifiera.
            creds = None

    # Si pas de creds valides, on tente un refresh si possible, sinon on relance un flow complet
    if not creds or not creds.valid:
        refreshed = False
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                refreshed = True
            except RefreshError:
                # invalid_grant (token expiré/révoqué) => on supprime l'ancien token et on réauthentifie
                try:
                    if os.path.exists(config.TOKEN_PATH):
                        os.remove(config.TOKEN_PATH)
                except OSError:
                    pass
                creds = None  # on forcera un nouveau flow ci-dessous

        if not refreshed:
            # Vérifier la présence du fichier credentials.json
            if not os.path.exists(config.CREDENTIALS_PATH):
                raise FileNotFoundError(
                    f"Fichier d'identifiants introuvable: {config.CREDENTIALS_PATH}. "
                    "Activez l'API Calendar, téléchargez credentials.json et placez-le au bon emplacement."
                )
            # Lancer un nouveau flow OAuth (ouvre le navigateur)
            flow = InstalledAppFlow.from_client_secrets_file(config.CREDENTIALS_PATH, SCOPES)
            # port=0 laisse le système choisir un port libre, pratique pour éviter les collisions
            creds = flow.run_local_server(port=0)
            # Sauvegarder le token pour les prochaines exécutions
            with open(config.TOKEN_PATH, "w", encoding="utf-8") as token:
                token.write(creds.to_json())

    return build("calendar", "v3", credentials=creds)


def add_event(summary, due_date_str):
    """Ajoute un événement d'une journée entière. Format de date : AAAA-MM-JJ."""
    service = get_calendar_service()
    event = {
        'summary': summary,
        'start': {'date': due_date_str, 'timeZone': 'Europe/Paris'},
        'end': {'date': due_date_str, 'timeZone': 'Europe/Paris'},
    }
    try:
        created_event = service.events().insert(calendarId='primary', body=event).execute()
        print(f"Agent Agenda: Événement '{summary}' créé avec succès.")
        return True
    except HttpError as error:
        print(f"Agent Agenda: Erreur lors de la création de l'événement: {error}")
        return False

def get_upcoming_events(max_results=10):
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    try:
        service = get_calendar_service()

        # Call the Calendar API to get the list of calendars
        calendar_list = service.calendarList().list().execute()
        all_events = []

        for calendar_list_entry in calendar_list.get('items', []):
            calendar_id = calendar_list_entry['id']
            now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
            events_result = service.events().list(calendarId=calendar_id, timeMin=now,
                                                  maxResults=max_results, singleEvents=True,
                                                  orderBy='startTime').execute()
            events = events_result.get('items', [])
            all_events.extend(events)

        if not all_events:
            return "Aucun événement à venir trouvé."

        # Sort all events by start time
        all_events.sort(key=lambda x: x['start'].get('dateTime', x['start'].get('date')))

        # Limit to max_results
        all_events = all_events[:max_results]

        event_list = ""
        for event in all_events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            event_list += f"{start} - {event['summary']}\n"
        return event_list

    except HttpError as error:
        return f"An error occurred: {error}"

def delete_event(summary_to_delete):
    """Trouve un événement par son nom et le supprime."""
    print(f"Agent Agenda: Recherche de l'événement contenant '{summary_to_delete}'...")
    service = get_calendar_service()
    all_events = get_upcoming_events(max_events=50) 
    
    event_to_delete = None
    for event in all_events:
        # On cherche une correspondance (insensible à la casse et partielle)
        if summary_to_delete.lower() in event['summary'].lower():
            event_to_delete = event
            print(f"Agent Agenda: Événement trouvé : '{event['summary']}'")
            break

    if event_to_delete:
        try:
            service.events().delete(calendarId='primary', eventId=event_to_delete['id']).execute()
            print(f"Agent Agenda: Événement '{event_to_delete['summary']}' supprimé avec succès.")
            return True
        except HttpError as error:
            print(f"Agent Agenda: Erreur lors de la suppression de l'événement: {error}")
            return False
    else:
        print(f"Agent Agenda: Aucun événement correspondant à '{summary_to_delete}' n'a été trouvé.")
        return False
