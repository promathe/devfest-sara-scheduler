# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware  # <--- 1. IMPORT THIS
# from pydantic import BaseModel
# from typing import List, Dict, Any, Optional
# from datetime import datetime
# import os
# from dotenv import load_dotenv
# load_dotenv()

# # Import our Graph
# from graph import app as graph_app
# from tools import validate_token

# # Load environment variables


# app = FastAPI()

# @app.middleware("http")
# async def log_requests(request, call_next):
#     print(f"Hit: {request.method} {request.url}")
#     response = await call_next(request)
#     return response


# # --- 2. ADD CORS MIDDLEWARE HERE ---
# # List of URLs that are allowed to talk to this API
# origins = [
#     "http://localhost:3000",      # Your Next.js local server
#     "http://127.0.0.1:3000",      # Alternative localhost IP
#     # Uncomment and add your production URL later
#     # "https://2bkkq8jk-3000.inc1.devtunnels.ms/"
#     "https://9sv4kqgl-3000.inc1.devtunnels.ms/"
# ]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,        # Whitelist these URLs
#     allow_credentials=True,       # Allow cookies/tokens
#     allow_methods=["*"],          # Allow all methods (GET, POST, OPTIONS, etc.)
#     allow_headers=["*"],          # Allow all headers
# )
# # -----------------------------------

# # Input Schema (Matches what frontend sends)
# class ChatRequest(BaseModel):
#     messages: List[Dict[str, Any]]  # Full chat history
#     user_token: str                 # Google Access Token
#     timezone: Optional[str] = "UTC"

# @app.post("/chat")
# async def chat_endpoint(req: ChatRequest):
#     try:
#         # Validate token before processing
#         if not validate_token(req.user_token):
#             raise HTTPException(
#                 status_code=401, 
#                 detail="Invalid or expired Google OAuth token. Please re-authenticate with Google."
#             )
        
#         lc_messages = to_lc_messages(req.messages)

#         result = graph_app.invoke({
#             "messages": lc_messages,   # ✅ FIX
#             "user_token": req.user_token,
#             "current_time": datetime.now().isoformat(),
#             "user_timezone": req.timezone,
#             "current_action": None,
#             "pending_details": None
#         })

#         last_message = result["messages"][-1]
#         return {"response": last_message.content}

#     except Exception as e:
#         print(f"Error: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# from langchain_core.messages import HumanMessage, AIMessage

# def to_lc_messages(messages):
#     lc = []
#     for m in messages:
#         if m.get("role") == "user":
#             lc.append(HumanMessage(content=m.get("content", "")))
#         elif m.get("role") == "assistant":
#             lc.append(AIMessage(content=m.get("content", "")))
#     return lc


# if __name__ == "__main__":
#     import uvicorn
#     # host="0.0.0.0" makes it accessible on your local network
#     uvicorn.run(app, host="0.0.0.0", port=8000)

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
import requests  # <--- Added for Google API calls
import os
from dotenv import load_dotenv

load_dotenv()

# Import our Graph
from graph import app as graph_app
from tools import validate_token

app = FastAPI()

@app.middleware("http")
async def log_requests(request, call_next):
    print(f"Hit: {request.method} {request.url}")
    response = await call_next(request)
    return response

# --- CORS MIDDLEWARE ---
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://9sv4kqgl-3000.inc1.devtunnels.ms/"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- INPUT SCHEMA ---
class ChatRequest(BaseModel):
    messages: List[Dict[str, Any]]
    user_token: str
    timezone: Optional[str] = "UTC"

# --- CHAT ENDPOINT ---
@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    try:
        if not validate_token(req.user_token):
            raise HTTPException(
                status_code=401, 
                detail="Invalid or expired Google OAuth token."
            )
        
        lc_messages = to_lc_messages(req.messages)

        result = graph_app.invoke({
            "messages": lc_messages,
            "user_token": req.user_token,
            "current_time": datetime.now().isoformat(),
            "user_timezone": req.timezone,
            "current_action": None,
            "pending_details": None
        })

        last_message = result["messages"][-1]
        return {"response": last_message.content}

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- UPCOMING EVENTS ENDPOINT (NEW) ---
@app.get("/events/upcoming")
async def get_upcoming_events(user_token: str = Query(..., alias="user_token")):
    try:
        # 1. Define IST explicitly
        IST = timezone(timedelta(hours=5, minutes=30))
        
        # 2. Get "Now" in IST
        now_ist = datetime.now(IST)
        
        # 3. FORCE START AT MIDNIGHT (The Critical Fix)
        # We strip the time and set it to 00:00:00. This captures ALL of "Today".
        start_of_today = now_ist.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 4. End Window = Start + 5 Days (Today + Next 4 Days)
        end_window = start_of_today + timedelta(days=5)
        
        # 5. Format for Google API
        # We use .isoformat() which keeps the "+05:30" offset.
        time_min = start_of_today.isoformat()
        time_max = end_window.isoformat()
        
        # 6. Call Google Calendar API Directly
        url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
        headers = {"Authorization": f"Bearer {user_token}"}
        params = {
            "timeMin": time_min,
            "timeMax": time_max,
            "singleEvents": "true",
            "orderBy": "startTime"
        }
        
        # Note: requests is blocking, but acceptable for this scale.
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            # Silently return empty list on token error instead of crashing UI
            print(f"Google API Error: {response.text}")
            return {"upcoming": []}
            
        items = response.json().get("items", [])
        
        # 7. Format Data for Frontend
        formatted_events = []
        
        for event in items:
            # Skip cancelled events
            if event.get("status") == "cancelled":
                continue
                
            # Get Start Time
            start_raw = event.get("start", {}).get("dateTime")
            end_raw = event.get("end", {}).get("dateTime")
            if not start_raw: 
                continue # Skip all-day events
                
            # Parse Dates Safely
            try:
                # Handle "Z" (UTC) vs Offsets (+05:30)
                # We standardize everything to IST for display
                if "Z" in start_raw:
                    dt_obj = datetime.fromisoformat(start_raw.replace("Z", "+00:00")).astimezone(IST)
                    dt_end = datetime.fromisoformat(end_raw.replace("Z", "+00:00")).astimezone(IST)
                else:
                    dt_obj = datetime.fromisoformat(start_raw)
                    dt_end = datetime.fromisoformat(end_raw)
                    
            except ValueError:
                continue 

            # Calculate "Human Readable" labels based on IST dates
            day_diff = (dt_obj.date() - now_ist.date()).days
            
            # Logic: Cap at Today + 4 days (Total 5 days)
            if day_diff > 4:
                continue
            
            if day_diff == 0:
                date_label = "Today"
            elif day_diff == 1:
                date_label = "Tomorrow"
            else:
                date_label = dt_obj.strftime("%a, %b %d") # e.g., "Mon, Jan 20"
            
            # Create Clean JSON Object
            formatted_events.append({
                "id": event.get("id"),
                "title": event.get("summary", "No Title"),
                "start_time": dt_obj.strftime("%I:%M %p"), # e.g. "02:00 PM"
                "end_time": dt_end.strftime("%I:%M %p"),
                "date_label": date_label,
                "is_urgent": "deadline" in event.get("summary", "").lower()
            })
            
        return {"upcoming": formatted_events}

    except Exception as e:
        print(f"Error fetching upcoming events: {e}")
        return {"upcoming": []}

# --- HELPERS ---
from langchain_core.messages import HumanMessage, AIMessage

def to_lc_messages(messages):
    lc = []
    for m in messages:
        if m.get("role") == "user":
            lc.append(HumanMessage(content=m.get("content", "")))
        elif m.get("role") == "assistant":
            lc.append(AIMessage(content=m.get("content", "")))
    return lc

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
