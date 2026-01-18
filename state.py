from typing import TypedDict, Annotated, List, Optional, Dict, Any
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    # 'add_messages' ensures new chat history is appended, not overwritten
    messages: Annotated[List[BaseMessage], add_messages]
    
    # Context variables passed from the Frontend
    user_token: str       # The Google OAuth Access Token (Required for Tools)
    current_time: str     # ISO string (e.g., "2026-01-20T10:00:00")
    user_timezone: str    # e.g., "Asia/Kolkata"
    
    # Optional: Track session ID for logging or refusal logic
    session_id: Optional[str]
    
    # Conversation context for multi-turn interactions
    current_action: Optional[str]  # e.g., "scheduling", "deleting"
    pending_details: Optional[Dict[str, Any]]  # store partial scheduling info

