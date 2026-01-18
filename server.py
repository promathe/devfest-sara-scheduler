from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware  # <--- 1. IMPORT THIS
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import os
from dotenv import load_dotenv
load_dotenv()

# Import our Graph
from graph import app as graph_app
from tools import validate_token

# Load environment variables


app = FastAPI()

@app.middleware("http")
async def log_requests(request, call_next):
    print(f"Hit: {request.method} {request.url}")
    response = await call_next(request)
    return response


# --- 2. ADD CORS MIDDLEWARE HERE ---
# List of URLs that are allowed to talk to this API
origins = [
    "http://localhost:3000",      # Your Next.js local server
    "http://127.0.0.1:3000",      # Alternative localhost IP
    # Uncomment and add your production URL later
    # "https://2bkkq8jk-3000.inc1.devtunnels.ms/"
    "https://9sv4kqgl-3000.inc1.devtunnels.ms/"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,        # Whitelist these URLs
    allow_credentials=True,       # Allow cookies/tokens
    allow_methods=["*"],          # Allow all methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],          # Allow all headers
)
# -----------------------------------

# Input Schema (Matches what frontend sends)
class ChatRequest(BaseModel):
    messages: List[Dict[str, Any]]  # Full chat history
    user_token: str                 # Google Access Token
    timezone: Optional[str] = "UTC"

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    try:
        # Validate token before processing
        if not validate_token(req.user_token):
            raise HTTPException(
                status_code=401, 
                detail="Invalid or expired Google OAuth token. Please re-authenticate with Google."
            )
        
        lc_messages = to_lc_messages(req.messages)

        result = graph_app.invoke({
            "messages": lc_messages,   # ✅ FIX
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
    # host="0.0.0.0" makes it accessible on your local network
    uvicorn.run(app, host="0.0.0.0", port=8000)