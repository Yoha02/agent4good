import asyncio
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from agent import root_agent

APP_NAME = "community_health_app"
USER_ID = "user1234"
SESSION_ID = "1234"

_session_service = None
_runner = None
_session = None

def _initialize_session():
    global _session_service, _runner, _session
    if _session_service is None:
        _session_service = InMemorySessionService()
        _session = asyncio.run(
            _session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
        )
        _runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=_session_service)

def call_agent(query: str) -> str:
    _initialize_session()
    content = types.Content(role="user", parts=[types.Part(text=query)])
    events = _runner.run(user_id=USER_ID, session_id=SESSION_ID, new_message=content)
    for event in events:
        if event.is_final_response():
            return event.content.parts[0].text
    return "No response received."

def run_interactive():
    print("=== COMMUNITY HEALTH & WELLNESS ASSISTANT ===")
    while True:
        query = input("You: ").strip()
        if query.lower() in ["exit", "quit"]:
            print("👋 Goodbye!")
            break
        print("\nProcessing...\n")
        print(call_agent(query))
        print("\n--------------------------------------------\n")

if __name__ == "__main__":
    run_interactive()
