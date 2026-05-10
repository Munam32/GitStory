# core/project_mapper.py
import requests
import json
from dotenv import load_dotenv
from config import MODEL
import os 
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL_NAME = MODEL


GLOBAL_MAP_PROMPT = """
You are a Lead Software Architect. I will provide you with a list of file paths and their summaries for a software project.
Your task is to write a "Project Map" that covers:

1. THE CORE PURPOSE: In 2 sentences, what does this app actually do?
2. ARCHITECTURAL STYLE: (e.g., MVC, Microservices, Layered, etc.)
3. THE DATA FLOW: How does data move from the entry point to the final output?
4. KEY COMPONENTS: Which files are the "brain" of the project?

Here is the file list and summaries:
{summaries_text}

Write the Project Map in a professional, clear, and narrative style.
"""

def generate_global_map(summaries: list) -> str:
    # Convert the list of summaries into a single block of text for the AI
    summaries_text = ""
    for s in summaries:
        summaries_text += f"FILE: {s['file_path']}\nSUMMARY: {s['summary']}\n\n"

    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
            data=json.dumps({
                "model": MODEL_NAME,
                "messages": [
                    {"role": "user", "content": GLOBAL_MAP_PROMPT.format(summaries_text=summaries_text)}
                ]
            })
        )
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"Error generating map: {str(e)}"