# config.py
EMBED_MODEL = "nvidia/llama-nemotron-embed-vl-1b-v2:free"
MODEL = "nvidia/nemotron-3-super-120b-a12b:free"
CHROMA_PATH = "./chroma_db"
MAX_FILE_SIZE_KB = 500        # skip files larger than this
MAX_COMMITS = 500             # only process last N commits
CHUNK_SIZE = 512              # tokens per chunk
CHUNK_OVERLAP = 50
SUMMARY_MAX_TOKENS = 150      # keep summaries short

MAX_SUMMARY_WORKERS = 5       # parallel threads for summarization
API_RETRY_ATTEMPTS = 3        # retries on OpenRouter failures
API_RETRY_WAIT_MIN = 2        # seconds
API_RETRY_WAIT_MAX = 10       # seconds
MAX_COMMITS = 500             # max commits to index from PyDriller
COMMIT_DIFF_MAX_CHARS = 2000  # truncate large diffs
