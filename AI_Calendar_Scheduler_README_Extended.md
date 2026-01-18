> **AI** **Calendar** **Scheduler** FastAPI + LangGraph + Google
> Calendar (with a Hugging Face LLM)
>
> This project is a small AI scheduling backend that chats with a user,
> checks intent, and then talks to Google Calendar to find free time,
> book events, delete events, search events, and even shift today’s
> schedule. It’s built with FastAPI + a LangGraph workflow and uses a
> Hugging Face-hosted LLM (Qwen 2.5 Coder Instruct).
>
> **Quick** **start** **(the** **60-second** **version)**
>
> 1\) Install deps: pip install -r requirements.txt 2) Add .env with
> HUGGINGFACEHUB_API_TOKEN=...
>
> 3\) Run: uvicorn server:app --reload --host 0.0.0.0 --port 8000 4)
> Open: http://localhost:8000/docs
>
> **What** **this** **service** **can** **do**
>
> • Read your calendar to understand what time is free (availability /
> free-busy style checks). • Find a best slot for a task duration before
> a deadline, inside working hours.
>
> • Book an event on Google Calendar (with clash detection). • Search
> events by query text.
>
> • Delete an event (by title and time window).
>
> • Shift the remaining schedule for today by N minutes (handy for
> “meeting ran late”).
>
> **Repo** **layout** **(who** **does** **what)**
>
> **File**
>
> server.py
>
> graph.py
>
> tools.py
>
> guardrail.py
>
> requirements.txt

**Purpose**

FastAPI entrypoint. Defines /chat and /events/upcoming, sets CORS,
formats messages, calls the gr

LangGraph workflow: guardrail -\> agent -\> tool execution loop.
Interprets tool calls emitted by the LL

Google Calendar tool functions using HTTP requests (availability,
booking, deletion, search, slot find

A lightweight YES/NO gate that checks whether the user message is about
calendar scheduling.

Python dependencies.

> Note: you may see files with suffixes like server (3).py or tools
> (3).py from iterative edits. Use the ones you actually run (usually
> the plain server.py that uvicorn imports).

AI Calendar Scheduler README Page 1

> **Prerequisites**
>
> • Python 3.10+ installed.
>
> • A Hugging Face access token (set as HUGGINGFACEHUB_API_TOKEN).
>
> • A Google OAuth access token from your frontend (sent to the backend
> as user_token).
>
> **Setup**
>
> python -m venv .venv \# mac/linux
>
> source .venv/bin/activate \# windows
>
> \# .venv\Scripts\activate
>
> pip install -r requirements.txt
>
> Create a .env file next to server.py:
>
> HUGGINGFACEHUB_API_TOKEN=hf_your_token_here
>
> **Run** **the** **API**
>
> Recommended (auto reload while you edit):
>
> uvicorn server:app --reload --host 0.0.0.0 --port 8000
>
> Or run directly:
>
> python server.py
>
> Open the docs in your browser:
>
> http://localhost:8000/docs
>
> Heads-up: don’t try to open http://0.0.0.0:8000 in the browser.
> 0.0.0.0 is a bind address (listen on all interfaces), not a
> destination. Use localhost or 127.0.0.1.

AI Calendar Scheduler README Page 2

> **API** **endpoints**
>
> **POST** **/chat** - runs the agent and returns a plain response
> string.
>
> curl -X POST http://localhost:8000/chat \\ -H "Content-Type:
> application/json" \\
>
> -d '{
>
> "messages":\[{"role":"user","content":"Book focus time tomorrow 3pm
> for 1 hour"}\], "user_token":"PASTE_GOOGLE_ACCESS_TOKEN",
>
> "timezone":"Asia/Kolkata" }'
>
> Request shape (JSON):
>
> {
>
> "messages": \[{"role": "user", "content": "..."}\], "user_token":
> "GOOGLE_OAUTH_ACCESS_TOKEN", "timezone": "UTC"
>
> }
>
> Response shape (JSON):
>
> {
>
> "response": "..." }
>
> **GET** **/events/upcoming?user_token=...** - returns upcoming events
> (about the next ~5 days) for display in a UI.
>
> curl
> "http://localhost:8000/events/upcoming?user_token=PASTE_GOOGLE_ACCESS_TOKEN"
>
> **How** **the** **agent** **works** **(simple** **mental** **model)**
>
> The graph has a small loop: first it runs a guardrail check, then the
> agent decides what to do next. If the agent wants calendar actions, it
> emits a tool call. The graph executes that tool, feeds results back to
> the agent, and repeats until the agent returns a final answer.
>
> **Tool** **call** **format**
>
> Tool calls are encoded inside the assistant message body using a
> delimiter format like this:
>
> \|\|\| {"tool": "find_best_slot", "args": { ... }} \|\|\|
>
> The graph code extracts that JSON and routes it to the matching
> function in tools.py.
>
> **Tools** **available**
>
> • check_availability(start_time, end_time, user_token)
>
> • book_event(summary, start_time, end_time, user_token) - includes
> clash detection • delete_event(event_title, start_time, end_time,
> user_token)
>
> • find_best_slot(duration_minutes, deadline, user_token,
> after_time=...) • search_events(query, user_token)

AI Calendar Scheduler README Page 3

> • shift_schedule(time_shift_minutes, user_token) - shifts remaining
> events today
>
> **Slot-finding** **rules** **(current** **behavior)**
>
> • Working hours are constrained (commonly 9 AM to 6 PM).
>
> • Some implementations add a lunch block (for example 1 PM to 2 PM).
>
> • Some implementations insert a buffer (for example 10 minutes)
> between tasks.
>
> • Some implementations cap the number of tasks per day to avoid
> overloading (burnout cap).

AI Calendar Scheduler README Page 4

> **Auth** **notes** **(tokens** **you** **need)** There are two
> separate tokens involved:
>
> **1)** **Hugging** **Face** **token**
>
> Used by the backend to call the Hugging Face Inference API. Put it in
> .env as HUGGINGFACEHUB_API_TOKEN.
>
> **2)** **Google** **OAuth** **access** **token**
>
> This comes from your frontend OAuth flow. The backend does not
> generate it. You pass it in each request as user_token, and the tool
> functions forward it to Google Calendar endpoints.
>
> If calendar calls fail with 401/403:
>
> • The access token may be expired - re-auth and retry.
>
> • The token may be missing required scopes for Calendar. • You may be
> hitting the wrong account / wrong token.
>
> **Troubleshooting**
>
> **“Site** **can’t** **be** **reached”**
>
> • Use http://localhost:8000/docs, not http://0.0.0.0:8000. • Make sure
> you are using http:// (not https).
>
> • Confirm the server is listening: curl -I http://127.0.0.1:8000/docs.
>
> • If you are in Docker/WSL/remote dev env, make sure port 8000 is
> forwarded/exposed.
>
> **“Model** **calls** **fail** **/** **no** **LLM** **response”**
>
> • Check HUGGINGFACEHUB_API_TOKEN is set (and loaded from .env).
>
> • If you get rate-limit style errors, slow down requests or switch to
> a smaller model / provider.
>
> **“Calendar** **tools** **aren’t** **being** **called”**
>
> • Verify the guardrail is returning YES for your prompt. If it returns
> NO, the agent won’t schedule. • Use explicit prompts like “Schedule”,
> “Book”, “Find a slot”, “Delete the event”.
>
> • Turn on server logging and print the raw agent message to see if
> tool call JSON is being emitted.
>
> **Known** **quirks** **(not** **blockers,** **just** **good** **to**
> **know)**
>
> • tools.py contains more than one find_best_slot definition. Python
> uses the last one in the file. • graph.py contains some duplicated
> imports/branches. It still runs but it’s worth cleaning later.
>
> • The server maps your UI-style messages into LangChain-style messages
> before invoking the graph.

AI Calendar Scheduler README Page 5

> **Quick** **demo** **script** **(3** **prompts)** If you want a clean
> demo run, try these in order:
>
> • “Show my upcoming events.” (hit /events/upcoming)
>
> • “Find me a 45-minute slot today after 2pm to review proposals.” •
> “Shift my remaining schedule by 15 minutes.”
>
> That’s it. If you want to polish further, the next easy wins are:
> remove duplicate functions, add safe tagging for created events, and
> add a preview-before-apply mode.

AI Calendar Scheduler README Page 6
