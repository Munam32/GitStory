# Testing GitStory

GitStory consists of a Next.js frontend and two Python FastAPI backends.

## 1. Prerequisites
- Python 3.9+
- Node.js 18+
- GitHub Personal Access Token (for private repos and analysis)
- Gemini / OpenAI API Keys (configured in `.env` or RAG config)

## 2. Backend Setup

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Start RAG Backend (Port 8000)
This backend handles repository indexing and RAG-based chat.
```bash
uvicorn server:app --host 0.0.0.0 --port 8000
```

### Start Analysis Backend (Port 8002)
This backend handles Timeline Narration, File Hotzones, and AI Code Review.
```bash
python api.py
```

## 3. Frontend Setup

### Install Dependencies
```bash
cd frontend
npm install
```

### Start Development Server
```bash
npm run dev
```
The app will be available at [http://localhost:3000](http://localhost:3000).

## 4. Features to Test

- **Dashboard (/)**: Index a repository and chat with its codebase.
- **Timeline (/timeline)**: Enter a GitHub URL to generate a narrated history of the project.
- **Hotzone (/hotzone)**: Visualize file churn and see which files are modified most frequently.
- **Review (/review)**: Get an AI-powered code review of recent commits (requires GitHub Token).

## 5. Environment Configuration
Ensure you have the necessary environment variables set up in a `.env` file in the root directory for the Python backends, and in `frontend/.env.local` for the Next.js app (especially for NextAuth).
