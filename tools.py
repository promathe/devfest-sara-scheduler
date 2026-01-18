import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Optional, Dict, Any

# CONFIG
DEFAULT_TZ = ZoneInfo("Asia/Calcutta")
GOOGLE_CAL_BASE = "https://www.googleapis.com/calendar/v3"

# ... [Keep your validate_token, _headers, _request, and _ensure_rfc3339 functions exactly as they are] ...
# (Copy them from your previous file or the blocks below)

def validate_token(token: str) -> bool:
    if not token or not isinstance(token, str) or len(token.strip()) == 0: return False
    if not token.startswith("ya29."): return False
    try:
        test_resp = requests.get("https://www.googleapis.com/oauth2/v1/tokeninfo", params={"access_token": token}, timeout=5)
        if test_resp.status_code == 200 and "https://www.googleapis.com/auth/calendar" in test_resp.json().get("scope", ""): return True
    except: pass
    return False

def _headers(token: str):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

def _request(method: str, url: str, token: str, json_body: dict = None, params: dict = None):
    try:
        resp = requests.request(method, url, headers=_headers(token), json=json_body, params=params)
        if 200 <= resp.status_code < 300:
            if resp.text: return resp.json()
            return {"status": "success"}
        return {"error": resp.text}
    except Exception as e: return {"error": str(e)}

def _ensure_rfc3339(date_str: str) -> str:
    if not date_str: return date_str
    try:
        dt = datetime.fromisoformat(date_str)
        if dt.tzinfo is None: dt = dt.replace(tzinfo=DEFAULT_TZ)
        return dt.isoformat()
    except ValueError:
        if not date_str.endswith("Z") and "+" not in date_str: return f"{date_str}Z"
        return date_str

# 1. LIST EVENTS (UPDATED: Shows IDs)
def list_events(user_token: str, days: int = 7) -> str:
    start = datetime.now(DEFAULT_TZ)
    end = start + timedelta(days=days)
    
    params = {
        "timeMin": start.isoformat(),
        "timeMax": end.isoformat(),
        "singleEvents": "true",
        "orderBy": "startTime"
    }
    
    data = _request("GET", f"{GOOGLE_CAL_BASE}/calendars/primary/events", user_token, params=params)
    
    if "error" in data: return f"Error listing events: {data['error']}"
    
    items = data.get("items", [])
    if not items: return "No upcoming events found."
    
    result = []
    for e in items:
        start_t = e.get("start", {}).get("dateTime", "") or e.get("start", {}).get("date", "")
        summary = e.get("summary", "Untitled")
        event_id = e.get("id") # <--- CAPTURE ID
        # RETURN ID TO THE AI
        result.append(f"- {start_t}: {summary} (ID: {event_id})")
    
    return "\n".join(result)

# 2. ADD EVENT (UPDATED: Returns ID)
def add_event(user_token: str, summary: str, start_iso: str, end_iso: str, recurrence: str = None) -> str:
    safe_start = _ensure_rfc3339(start_iso)
    safe_end = _ensure_rfc3339(end_iso)

    body = {
        "summary": summary,
        "start": {"dateTime": safe_start, "timeZone": str(DEFAULT_TZ)},
        "end": {"dateTime": safe_end, "timeZone": str(DEFAULT_TZ)}
    }
    if recurrence:
        body["recurrence"] = [recurrence]
    
    data = _request("POST", f"{GOOGLE_CAL_BASE}/calendars/primary/events", user_token, json_body=body)
    if "error" in data: return f"Error adding event: {data['error']}"
    
    # <--- RETURN ID SO AI KNOWS IT IMMEDIATELY
    return f"Event created. ID: {data.get('id')} | Link: {data.get('htmlLink')}"

# 3. UPDATE EVENT
def update_event(user_token: str, event_id: str, summary: str = None, start_iso: str = None, end_iso: str = None) -> str:
    body = {}
    if summary: body["summary"] = summary
    if start_iso: body["start"] = {"dateTime": _ensure_rfc3339(start_iso), "timeZone": str(DEFAULT_TZ)}
    if end_iso: body["end"] = {"dateTime": _ensure_rfc3339(end_iso), "timeZone": str(DEFAULT_TZ)}
    
    data = _request("PATCH", f"{GOOGLE_CAL_BASE}/calendars/primary/events/{event_id}", user_token, json_body=body)
    if "error" in data: return f"Error updating event: {data['error']}"
    return "Event updated successfully."

# 4. DELETE EVENT
def delete_event(user_token: str, event_id: str) -> str:
    data = _request("DELETE", f"{GOOGLE_CAL_BASE}/calendars/primary/events/{event_id}", user_token)
    if "error" in data: 
        # Help the AI understand 404
        if "404" in str(data) or "Not Found" in str(data):
            return "Error: Event not found. Please list events to get the correct ID."
        return f"Error deleting event: {data['error']}"
    return "Event deleted successfully."

# 5. RESCHEDULE EVENT
def reschedule_event(user_token: str, old_event_id: str, new_summary: str, new_start_iso: str, new_end_iso: str) -> str:
    # Delete the old event
    delete_response = delete_event(user_token, old_event_id)
    if "Error" in delete_response:
        return f"Failed to reschedule: {delete_response}"

    # Add the new event
    add_response = add_event(user_token, new_summary, new_start_iso, new_end_iso)
    if "Error" in add_response:
        return f"Deleted old event but failed to create new one: {add_response}"

    return "Event rescheduled successfully."

# 6. DELETE EVENTS IN RANGE
def delete_events_in_range(user_token: str, start_date: str, end_date: str) -> str:
    valid_start = _ensure_rfc3339(start_date)
    valid_end = _ensure_rfc3339(end_date)
    
    params = {
        "timeMin": valid_start,
        "timeMax": valid_end,
        "singleEvents": "true",
        "orderBy": "startTime"
    }

    data = _request("GET", f"{GOOGLE_CAL_BASE}/calendars/primary/events", user_token, params=params)

    if "error" in data:
        if "Bad Request" in str(data):
             return f"Error: Google rejected dates. Tried: {valid_start} to {valid_end}"
        return f"Error listing events: {data['error']}"

    items = data.get("items", [])
    if not items: return "No events found in range."

    count = 0
    for event in items:
        if delete_event(user_token, event.get("id")) == "Event deleted successfully.":
            count += 1
            
    return f"Deleted {count} events."