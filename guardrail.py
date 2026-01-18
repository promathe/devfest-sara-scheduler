from langchain_huggingface import HuggingFaceEndpoint
from dotenv import load_dotenv

load_dotenv()

llm = HuggingFaceEndpoint(
    repo_id="Qwen/Qwen2.5-Coder-32B-Instruct",
    task="text-generation",
    max_new_tokens=10,
    temperature=0.1
)

def validate_intent(text: str) -> bool:
    prompt = f"""
    Is this text related to calendars, scheduling, meetings, or time?
    Text: "{text}"
    Reply only YES or NO.
    """
    try:
        resp = llm.invoke(prompt)
        return "YES" in resp.upper()
    except:
        return True # Fail open if API errors
