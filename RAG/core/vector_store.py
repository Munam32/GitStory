# core/vector_store.py
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
        """
        OpenRouter/OpenAI compatible embedding call.
        """
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
            
            # Return just the raw embedding vectors
            return [record["embedding"] for record in data["data"]]
        except Exception as e:
            print(f"❌ OpenRouter Embedding Error: {e}")
            raise

# Initialize the free cloud-based embedding brain
OPENROUTER_EF = OpenRouterEmbeddingFunction()

class GitStoryDB:
    def __init__(self, db_path="./chroma_db"):
        """Initializes ChromaDB with separate collections for summaries and code."""
        self.client = chromadb.PersistentClient(path=db_path)
        
        # Collection for the 'Map' (Summaries)
        self.summary_col = self.client.get_or_create_collection(
            name="file_summaries", 
            embedding_function=OPENROUTER_EF
        )
        
        # Collection for the 'Evidence' (AST Chunks)
        self.code_col = self.client.get_or_create_collection(
            name="code_chunks", 
            embedding_function=OPENROUTER_EF
        )

    def add_summaries(self, summaries: list):
        """
        Stores file summaries.
        Expects list of: {'file_path': str, 'summary': str, 'language': str}
        """
        if not summaries: return

        ids = [s['file_path'] for s in summaries]
        docs = [s['summary'] for s in summaries]
        metadatas = [{"language": s['language'], "file_path": s['file_path']} for s in summaries]
        
        self.summary_col.upsert(ids=ids, documents=docs, metadatas=metadatas)
        print(f"✅ Stored {len(ids)} file summaries via OpenRouter.")

    def add_ast_chunks(self, chunks: list):
        """
        Stores AST chunks from your chunker.py.
        """
        if not chunks: return

        # Create unique IDs (e.g., 'src/main.py_chunk_0')
        ids = [f"{c['file_path']}_chunk_{i}" for i, c in enumerate(chunks)]
        docs = [c['text'] for c in chunks]
        
        # Storing AST metadata for detailed retrieval
        metadatas = [{
            "file_path": c['file_path'],
            "node_type": c['type'],
            "name": c.get('name', 'anonymous'),
            "line_range": f"{c['start_line']}-{c['end_line']}"
        } for c in chunks]

        self.code_col.upsert(ids=ids, documents=docs, metadatas=metadatas)
        print(f"✅ Stored {len(ids)} AST chunks via OpenRouter.")