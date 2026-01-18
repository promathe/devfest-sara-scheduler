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

def get_system_prompt(current_time_str: str) -> str:
    return f"""You are an AI Personal Planning Assistant.

Current Date & Time: {current_time_str}

TOOLS AVAILABLE (Output ONLY JSON):
1. LIST EVENTS: {{"tool": "list_events", "args": {{"days": 7}}}}
2. ADD EVENT:   {{"tool": "add_event", "args": {{"summary": "Title", "start_iso": "...", "end_iso": "..."}}}}
3. DELETE:      {{"tool": "delete_event", "args": {{"event_id": "..."}}}}
4. RESCHEDULE:  {{"tool": "reschedule_event", "args": {{"old_event_id": "...", "new_summary": "...", "new_start_iso": "...", "new_end_iso": "..."}}}}
5. MASS DELETE: {{"tool": "delete_events_in_range", "args": {{"start_date": "...", "end_date": "..."}}}}

CRITICAL RULES:
1. NO TIME? NO TOOL. If user omits time/date, ASK them. Do not guess.
2. NO ID? FIND IT. If rescheduling/deleting and you lack the 'event_id', call 'list_events' first.
3. FORMAT: ISO 8601 with timezone (e.g., "+05:30").

--- FEW-SHOT EXAMPLES ---

Scenario 1: Missing Information
User: "Book a client call."
AI: "Sure, what day and time would you like to schedule that?"
(Reason: No time provided -> Ask clarification, do not call tool.)

Scenario 2: Simple Booking (Relative Date)
User: "Schedule 'Gym' for tomorrow at 6pm for 1 hour."
(Assuming 'Tomorrow' is 2026-01-20)
AI: {{"tool": "add_event", "args": {{"summary": "Gym", "start_iso": "2026-01-20T18:00:00+05:30", "end_iso": "2026-01-20T19:00:00+05:30"}}}}

Scenario 3: Rescheduling (Unknown ID)
User: "Move the 'Weekly Sync' to 4pm."
(Reason: You cannot reschedule without an ID. You must find it first.)
AI: {{"tool": "list_events", "args": {{"days": 7}}}}

Scenario 4: Mass Delete
User: "Clear my schedule for the rest of January."
(Assuming 'Rest of Jan' is Now to Jan 31)
AI: {{"tool": "delete_events_in_range", "args": {{"start_date": "2026-01-19T13:00:00+05:30", "end_date": "2026-01-31T23:59:59+05:30"}}}}

Scenario 5: Recurring Event
User: "Team standup every Monday at 10am for 4 weeks."
AI: {{"tool": "add_event", "args": {{"summary": "Team Standup", "start_iso": "2026-01-26T10:00:00+05:30", "end_iso": "2026-01-26T10:30:00+05:30", "recurrence": "RRULE:FREQ=WEEKLY;COUNT=4"}}}}
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