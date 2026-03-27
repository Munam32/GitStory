# core/query_engine.py
import requests
import json
import os
from dotenv import load_dotenv
from core.vector_store import GitStoryDB
from config import MODEL

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

class GitStoryEngine:
    def __init__(self):
        self.db = GitStoryDB()
        self.model = MODEL
        
        # Load the Global Map (The North Star)
        try:
            with open("project_map.json", "r" , encoding="utf-8") as f:
                self.project_map = f.read()
        except FileNotFoundError:
            self.project_map = "Global project architecture map not yet generated."

    def ask(self, question: str):
        print(f"🧐 Searching for answers to: '{question}'")

        # STEP 1: Search Summaries to identify relevant files
        # This prevents the AI from looking at UI code when you ask about Database logic.
        summary_results = self.db.summary_col.query(
            query_texts=[question],
            n_results=3
        )
        relevant_files = summary_results['ids'][0]
        file_context = "\n".join(summary_results['documents'][0])

        print(f"📂 Focused search on: {', '.join(relevant_files)}")

        # STEP 2: Search AST Chunks ONLY within those files
        # This is where your tree-sitter metadata pays off!
        code_results = self.db.code_col.query(
            query_texts=[question],
            n_results=5,
            where={"file_path": {"$in": relevant_files}}
        )
        code_context = ""
        for i, doc in enumerate(code_results['documents'][0]):
            meta = code_results['metadatas'][0][i]
            code_context += f"\nFILE: {meta['file_path']} ({meta['node_type']}: {meta['name']})\n{doc}\n"

        # STEP 3: The Narrative Prompt
        prompt = f"""
        You are a 'Coding Partner' chatbot. Your goal is to provide a fast, technical, and direct answer based on the repository context.
        
        [GLOBAL CONTEXT]
        {self.project_map}
        
        [CODE SNIPPETS]
        {code_context}
        
        USER QUESTION: {question}
        
        RESPONSE RULES:
        1. Be concise. No fluff. No 'Senior Architect' intros.
        2. If there's code that answers the question, show it immediately.
        3. Use file paths as headers.
        4. If you don't know, just say "I don't see that in the current index."
        """

        # STEP 4: Call Nemotron
        try:
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
                data=json.dumps({
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}]
                })
            )
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            return f"Error narrating the story: {str(e)}"