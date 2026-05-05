import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class NarrationGenerator:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key,
        )
        self.model = "nvidia/nemotron-3-nano-30b-a3b:free"

    def generate_narration(self, commits_data: list):
        print(f"--- DEBUG: Starting generate_narration with {len(commits_data)} commits ---")
        if not commits_data:
            print("--- DEBUG: No commits found. Returning error. ---")
            return {"error": "No commit data found."}

        prompt = f"""
        You are a project historian and tech lead. Analyze the following commit history of a software project.
        Identify 5-8 major benchmarks or milestones (e.g., Project Start, Major Feature, Refactor, Performance Boost).
        For each benchmark, provide:
        1. A catchy Title.
        2. A short Description (Narration).
        3. A 'Nature' (e.g., 'feature', 'refactor', 'fix', 'milestone').
        4. An 'Urgency' level (1-5).
        5. A representative Date (from the commits).
        6. The 'commit_hash' of the most relevant commit.

        Commit Data Summary:
        {json.dumps(commits_data, indent=2)}

        Return ONLY a JSON object with this structure:
        {{
          "project_summary": "Overall story in 2 sentences",
          "benchmarks": [
            {{
              "title": "string",
              "description": "string",
              "nature": "string",
              "urgency": number,
              "date": "ISO string",
              "commit_hash": "string",
              "impact_score": number (0-100 based on insertions/deletions)
            }}
          ]
        }}
        """

        try:
            print(f"--- DEBUG: Sending request to LLM (model: {self.model})... ---")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            print("--- DEBUG: LLM response received. ---")
            # Basic cleaning of LLM response to ensure valid JSON
            content = response.choices[0].message.content.strip()
            print(f"--- DEBUG: Content length: {len(content)} ---")
            
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            
            parsed_json = json.loads(content)
            print(f"--- DEBUG: Successfully parsed JSON. Benchmarks found: {len(parsed_json.get('benchmarks', []))} ---")
            return parsed_json
        except Exception as e:
            print(f"--- DEBUG ERROR: Error generating narration: {e} ---")
            return {"error": str(e)}
