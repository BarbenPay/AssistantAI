import datetime
import os.path
import config
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
    if os.path.exists(config.TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(config.TOKEN_PATH, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(config.CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(config.TOKEN_PATH, "w") as token:
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

def get_upcoming_events(max_events=10):
    """Liste les prochains événements du calendrier et retourne leurs IDs."""
    service = get_calendar_service()
    upcoming_events = []
    try:
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        events_result = service.events().list(
            calendarId="primary", timeMin=now, maxResults=max_events,
            singleEvents=True, orderBy="startTime"
        ).execute()
        events = events_result.get("items", [])
        
        if not events:
            return []

        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            upcoming_events.append({"id": event["id"], "start": start, "summary": event["summary"]})
        
    except HttpError as error:
        print(f"Agent Agenda: Erreur lors de la lecture des événements: {error}")
    
    return upcoming_events

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
