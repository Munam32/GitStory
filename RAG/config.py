# config.py
EMBED_MODEL = "BAAI/bge-small-en-v1.5"
MODEL = "nvidia/nemotron-3-super-120b-a12b:free"
CHROMA_PATH = "./chroma_db"
MAX_FILE_SIZE_KB = 500        # skip files larger than this
MAX_COMMITS = 500             # only process last N commits
CHUNK_SIZE = 512              # tokens per chunk
CHUNK_OVERLAP = 50
SUMMARY_MAX_TOKENS = 150      # keep summaries short

