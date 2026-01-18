import os
import json # <--- IMPORT JSON
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo # <--- IMPORT ZONEINFO
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage, AIMessage
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from dotenv import load_dotenv

from state import AgentState
from guardrail import validate_intent
import tools

load_dotenv()

# Model setup
llm = HuggingFaceEndpoint(
    repo_id="Qwen/Qwen2.5-Coder-32B-Instruct",
    task="text-generation",
    max_new_tokens=512,
    temperature=0.1,
    huggingfacehub_api_token=os.getenv("HUGGINGFACEHUBAPITOKEN")
)
chat_model = ChatHuggingFace(llm=llm)

# --- FIX 1: DYNAMIC PROMPT FUNCTION ---
def get_system_prompt(current_time_str: str) -> str:
    return f"""You are an AI Personal Planning Assistant.

Current Date & Time: {current_time_str}

You have access to the following tools. To use a tool, you must output ONLY valid JSON.

1. LIST EVENTS (Check availability):
   {{"tool": "list_events", "args": {{"days": 7}}}}

2. ADD EVENT (Schedule a task):
   {{"tool": "add_event", "args": {{"summary": "Client Call", "start_iso": "2026-01-20T10:00:00+05:30", "end_iso": "2026-01-20T11:00:00+05:30"}}}}

3. DELETE SINGLE EVENT (Remove one specific item):
   {{"tool": "delete_event", "args": {{"event_id": "eventId123"}}}}

4. MASS DELETE (Clear a range of time):
   {{"tool": "delete_events_in_range", "args": {{"start_date": "2026-01-01T00:00:00+05:30", "end_date": "2026-02-01T00:00:00+05:30"}}}}

5. RESCHEDULE EVENT (Move an event):
   {{"tool": "reschedule_event", "args": {{"old_event_id": "eventId123", "new_summary": "Client Call", "new_start_iso": "2026-01-22T14:00:00+05:30", "new_end_iso": "2026-01-22T15:00:00+05:30"}}}}

RULES:
- DATES: Always use ISO 8601 format with a timezone offset (e.g., "+05:30"). NEVER output a date without an offset (like "2026-01-01T10:00:00").
- MASS ACTIONS: If the user says "clear today", "delete everything this week", or "wipe January", USE 'delete_events_in_range'. Calculate the start and end times based on the 'Current Date & Time' provided above.
- RECURRENCE: If asked for a recurring event, add "recurrence": "RRULE:FREQ=WEEKLY;COUNT=10" to the args.
- RESPONSE: If you need more info, just ask naturally. If you are using a tool, output ONLY the JSON.
"""

def agent_node(state: AgentState):
    # Calculate current time for the prompt
    now = datetime.now(ZoneInfo("Asia/Calcutta"))
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")
    
    # Generate the prompt with the dynamic time
    sys_msg = SystemMessage(content=get_system_prompt(now_str))
    
    # Prepend the system message to the chat history
    messages = [sys_msg] + state["messages"]

    # Call the LLM
    resp = chat_model.invoke(messages)
    return {"messages": [resp]}

def tool_node(state: AgentState):
    last_msg = state["messages"][-1].content
    token = state["user_token"]

    try:
        # Extract JSON using Regex
        json_match = re.search(r"\{.*\}", last_msg, re.DOTALL)
        if not json_match:
            return {"messages": [AIMessage(content="Please provide more details about your task.")]}

        # --- FIX 3: USE JSON.LOADS INSTEAD OF EVAL ---
        # Qwen might output 'true' (json) which fails in eval() (expects 'True')
        cmd = json.loads(json_match.group(0)) 
        
        tool = cmd.get("tool")
        args = cmd.get("args", {})

        if tool == "list_events":
            res = tools.list_events(token, **args)
        elif tool == "add_event":
            res = tools.add_event(token, **args)
        elif tool == "update_event":
            res = tools.update_event(token, **args)
        elif tool == "delete_event":
            res = tools.delete_event(token, **args)
        elif tool == "reschedule_event":
            res = tools.reschedule_event(token, **args)
        elif tool == "delete_events_in_range":
            res = tools.delete_events_in_range(token, **args)
        else:
            res = f"Unknown tool: {tool}"

        return {"messages": [AIMessage(content=f"Calendar Tool Output: {res}")]}

    except json.JSONDecodeError:
        return {"messages": [AIMessage(content="Error: The AI generated invalid JSON. Please try again.")]}
    except Exception as e:
        return {"messages": [AIMessage(content=f"Error executing tool: {str(e)}")]}

def router(state: AgentState):
    last_msg = state["messages"][-1].content
    if "{" in last_msg and "tool" in last_msg:
        return "tools"
    return END

# Build workflow
workflow = StateGraph(AgentState)
workflow.add_node("agent", agent_node)
workflow.add_node("tools", tool_node)

workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", router, {"tools": "tools", END: END})
workflow.add_edge("tools", "agent")

app = workflow.compile()