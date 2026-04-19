# core/engine.py
import asyncio
import requests
import json
import os
from dotenv import load_dotenv
from core.vector_store import GitStoryDB
from config import MODEL

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Default directory (relative to wherever the server is launched from)
DEFAULT_MAPS_DIR = "./project_maps"


class GitStoryEngine:
    def __init__(self, repo_name: str = "default", db_path: str = "./chroma_db",
                 maps_dir: str = DEFAULT_MAPS_DIR):
        self.repo_name = repo_name
        self.db = GitStoryDB(db_path=db_path, repo_name=repo_name)
        self.model = MODEL
        self.history = []

        # Load the per-repo Global Map (The North Star)
        map_path = os.path.join(maps_dir, f"{repo_name}.json")
        try:
            with open(map_path, "r", encoding="utf-8") as f:
                self.project_map = f.read()
        except FileNotFoundError:
            self.project_map = "Global project architecture map not yet generated."

    def _build_prompt(self, question: str) -> tuple[str, str, str]:
        """
        Runs the three-step RAG retrieval and returns
        (file_context, code_context, history_context).
        """
        # STEP 1: Search Summaries to identify relevant files
        summary_results = self.db.summary_col.query(
            query_texts=[question],
            n_results=min(3, self.db.summary_col.count() or 1)
        )
        relevant_files = summary_results['ids'][0]
        file_context = "\n".join(summary_results['documents'][0])

        # STEP 2: Search AST Chunks ONLY within those files
        code_context = ""
        if relevant_files:
            code_results = self.db.code_col.query(
                query_texts=[question],
                n_results=5,
                where={"file_path": {"$in": relevant_files}}
            )
            for i, doc in enumerate(code_results['documents'][0]):
                meta = code_results['metadatas'][0][i]
                code_context += (
                    f"\nFILE: {meta['file_path']} "
                    f"({meta['node_type']}: {meta['name']})\n{doc}\n"
                )

        # STEP 3: Search commit history
        history_context = ""
        try:
            history_results = self.db.history_col.query(
                query_texts=[question],
                n_results=min(4, self.db.history_col.count() or 1)
            )
            for i, doc in enumerate(history_results['documents'][0]):
                meta = history_results['metadatas'][0][i]
                history_context += (
                    f"\nCOMMIT {meta['hash']} by {meta['author']} on {meta['date']}: "
                    f"{meta['commit_msg']}\nFILE: {meta['file']}\n{doc}\n"
                )
        except Exception:
            history_context = ""  # history not indexed yet — silent fallback

        return file_context, code_context, history_context

    def _format_prompt(self, question: str, code_context: str, history_context: str) -> str:
        return f"""You are a helpful and friendly 'Coding Partner' AI. Your goal is to explain the repository clearly and conversationally, like a senior developer mentoring a teammate.

[GLOBAL CONTEXT]
{self.project_map}

[CODE SNIPPETS]
{code_context}

[COMMIT HISTORY]
{history_context if history_context else "No commit history indexed yet."}

USER QUESTION: {question}

RESPONSE RULES:
1. Be conversational and approachable. Synthesize the provided context into a clear, easy-to-read explanation.
2. Don't just paste raw text; summarize what the files actually do in plain English.
3. Use file paths as headers when referencing specific parts of the codebase.
4. If there is relevant code that helps explain the answer, show brief snippets.
5. If the answer isn't in the context, politely say "I don't see that in the current repo."
"""

    def ask(self, question: str) -> str:
        """Synchronous (non-streaming) query."""
        print(f"Searching for answers to: '{question}'")
        _, code_context, history_context = self._build_prompt(question)
        prompt = self._format_prompt(question, code_context, history_context)

        self.history.append({"role": "user", "content": prompt})
        try:
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
                json={"model": self.model, "messages": self.history}
            )
            response.raise_for_status()
            answer = response.json()['choices'][0]['message']['content']
            self.history.append({"role": "assistant", "content": answer})
            return answer
        except Exception as e:
            self.history.pop()
            return f"Error narrating the story: {str(e)}"

    async def ask_stream(self, question: str):
        """
        Async generator that streams the AI response token-by-token using a
        background thread + asyncio.Queue so tokens are forwarded as they arrive
        rather than buffered until the full response is ready.
        Yields SSE-formatted strings: "data: {\"token\": \"...\"}\n\n"
        """
        print(f"Streaming answer for: '{question}'")

        loop = asyncio.get_event_loop()

        # ── Retrieval (blocking) in executor ────────────────────────────────
        _, code_context, history_context = await loop.run_in_executor(
            None, self._build_prompt, question
        )

        prompt = self._format_prompt(question, code_context, history_context)
        self.history.append({"role": "user", "content": prompt})

        # ── Streaming via queue ──────────────────────────────────────────────
        queue: asyncio.Queue = asyncio.Queue()
        full_answer_parts: list[str] = []

        def _stream_worker():
            """Runs in a thread; pushes tokens into the asyncio queue."""
            try:
                resp = requests.post(
                    url="https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": self.history,
                        "stream": True,
                    },
                    stream=True,
                )
                resp.raise_for_status()
                for raw_line in resp.iter_lines():
                    if not raw_line:
                        continue
                    line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else raw_line
                    if line == "data: [DONE]":
                        break
                    if line.startswith("data: "):
                        try:
                            chunk_data = json.loads(line[6:])
                            token = chunk_data["choices"][0].get("delta", {}).get("content", "")
                            if token:
                                full_answer_parts.append(token)
                                asyncio.run_coroutine_threadsafe(queue.put(token), loop)
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue
            except Exception as e:
                asyncio.run_coroutine_threadsafe(queue.put(e), loop)
            finally:
                asyncio.run_coroutine_threadsafe(queue.put(None), loop)  # sentinel

        # Launch blocking network call in thread pool
        loop.run_in_executor(None, _stream_worker)

        # ── Drain the queue and yield tokens ────────────────────────────────
        try:
            while True:
                item = await queue.get()
                if item is None:                          # stream finished
                    break
                if isinstance(item, Exception):           # stream error
                    self.history.pop()
                    yield f"data: {json.dumps({'error': str(item)})}\n\n"
                    return
                yield f"data: {json.dumps({'token': item})}\n\n"

            self.history.append({"role": "assistant", "content": "".join(full_answer_parts)})
            yield "data: [DONE]\n\n"

        except asyncio.CancelledError:
            # Client disconnected early
            self.history.pop()
            raise

    def reset_history(self):
        """Clear conversation memory for a fresh session."""
        self.history = []
