# core/vector_store.py
import re
import chromadb
import requests
import os
from dotenv import load_dotenv
from chromadb import EmbeddingFunction, Documents, Embeddings

load_dotenv()

# ── Custom OpenRouter Embedding Function ──────────────────
class OpenRouterEmbeddingFunction(EmbeddingFunction):
    """
    Uses OpenRouter's API to generate embeddings.
    This bypasses the need for local model downloads.
    """
    def __init__(self, model_name="nvidia/llama-nemotron-embed-vl-1b-v2:free"):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.model_name = model_name
        self.url = "https://openrouter.ai/api/v1/embeddings"

    def __call__(self, input: Documents) -> Embeddings:
        try:
            response = requests.post(
                url=self.url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model_name,
                    "input": input,
                }
            )
            response.raise_for_status()
            data = response.json()
            return [record["embedding"] for record in data["data"]]
        except Exception as e:
            print(f"❌ OpenRouter Embedding Error: {e}")
            raise

# Initialize the free cloud-based embedding brain
OPENROUTER_EF = OpenRouterEmbeddingFunction()


def _safe_collection_name(repo_name: str) -> str:
    """
    Convert a repo name or URL fragment into a ChromaDB-safe collection prefix.
    ChromaDB collection names must be 3-63 chars, alphanumeric + underscores/hyphens,
    start/end with alphanumeric.
    """
    # Strip full URL down to 'owner_repo' style
    name = repo_name.strip("/").split("/")[-1]
    # Replace non-alphanumeric chars with underscore
    name = re.sub(r"[^a-zA-Z0-9_-]", "_", name)
    # Truncate so prefix + suffix stays under 63 chars (suffix is '_summaries' = 10)
    name = name[:50]
    # Ensure it starts with a letter
    if name and not name[0].isalpha():
        name = "r_" + name
    return name or "default"


class GitStoryDB:
    def __init__(self, db_path="./chroma_db", repo_name="default"):
        """
        Initializes ChromaDB with per-repo namespaced collections.
        repo_name: short identifier (e.g. 'myrepo' or 'owner/myrepo') used to
                   namespace collections so multiple repos don't collide.
        """
        self.repo_name = repo_name
        prefix = _safe_collection_name(repo_name)
        self.client = chromadb.PersistentClient(path=db_path)

        # Collection for the 'Map' (Summaries)
        self.summary_col = self.client.get_or_create_collection(
            name=f"{prefix}_summaries",
            embedding_function=OPENROUTER_EF
        )

        # Collection for the 'Evidence' (AST Chunks)
        self.code_col = self.client.get_or_create_collection(
            name=f"{prefix}_chunks",
            embedding_function=OPENROUTER_EF
        )

        # Collection for commit history (PyDriller)
        self.history_col = self.client.get_or_create_collection(
            name=f"{prefix}_history",
            embedding_function=OPENROUTER_EF
        )

    def add_summaries(self, summaries: list):
        """
        Stores file summaries.
        Expects list of: {'file_path': str, 'summary': str, 'language': str}
        """
        if not summaries:
            return
        ids = [s['file_path'] for s in summaries]
        docs = [s['summary'] for s in summaries]
        metadatas = [{"language": s['language'], "file_path": s['file_path']} for s in summaries]
        self.summary_col.upsert(ids=ids, documents=docs, metadatas=metadatas)
        print(f"✅ Stored {len(ids)} file summaries via OpenRouter.")

    def add_ast_chunks(self, chunks: list):
        """
        Stores AST chunks from chunker.py.
        """
        if not chunks:
            return
        ids = [f"{c['file_path']}_chunk_{i}" for i, c in enumerate(chunks)]
        docs = [c['text'] for c in chunks]
        metadatas = [{
            "file_path": c['file_path'],
            "node_type": c['type'],
            "name": c.get('name', 'anonymous'),
            "line_range": f"{c['start_line']}-{c['end_line']}"
        } for c in chunks]
        self.code_col.upsert(ids=ids, documents=docs, metadatas=metadatas)
        print(f"✅ Stored {len(ids)} AST chunks via OpenRouter.")

    def add_commit_history(self, commits: list):
        """
        Stores PyDriller commit+diff records.
        Expects list of dicts from history_indexer.py
        """
        if not commits:
            return
        BATCH_SIZE = 50  # OpenRouter embedding API limit guard
        for i in range(0, len(commits), BATCH_SIZE):
            batch = commits[i:i + BATCH_SIZE]
            ids = [c['id'] for c in batch]
            docs = [c['document'] for c in batch]
            metadatas = [c['metadata'] for c in batch]
            self.history_col.upsert(ids=ids, documents=docs, metadatas=metadatas)
            print(f"✅ Stored commit batch {i // BATCH_SIZE + 1} ({len(batch)} records).")
