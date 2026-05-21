# Cognitive Challenge Agent (CCA)

A local-first, multi-agent system that challenges your ideas through adversarial debate, web-grounded research, and Socratic dialogue. Your reasoning history is stored privately in a local vector database (ChromaDB).

For security architecture and governance details, see [docs/security.md](docs/security.md).

## Prerequisites

- Python 3.11+
- API keys:
  - [Google AI Studio](https://aistudio.google.com/) — Gemini LLM and embeddings (`GOOGLE_API_KEY`)
  - [Tavily](https://tavily.com/) — web research (`TAVILY_API_KEY`)

## Setup

1. **Clone the repository**

   ```bash
   git clone <your-repo-url>
   cd "Cognitive Challenge Agent (CCA)"
   ```

2. **Create a virtual environment and install dependencies**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and set your real API keys. The `.env` file is ignored by git and must not be uploaded to GitHub.

4. **Run the backend** (FastAPI + LangGraph, bound to localhost only)

   ```bash
   python main.py
   ```

   The API listens at `http://127.0.0.1:8000`.

5. **Run the UI** (in a second terminal, with the venv activated)

   ```bash
   streamlit run ui.py
   ```

   Open the URL Streamlit prints (typically `http://localhost:8501`).

## Project layout

| File / directory | Purpose |
|------------------|---------|
| `main.py` | FastAPI server and LangGraph workflow |
| `agents.py` | CrewAI agent definitions |
| `memory.py` | ChromaDB semantic memory |
| `tools.py` | Tavily web search |
| `ui.py` | Streamlit frontend |
| `cca_chroma/` | Local vector store (created at runtime; not in git) |
| `.env` | API keys (local only; not in git) |

## Security notes

- The backend binds to `127.0.0.1` only — it is not exposed on your LAN by default.
- User thoughts and cognitive profiles live in `cca_chroma/` on disk. Keep that directory private and consider full-disk encryption.
- Rotate API keys if they are ever committed or shared by mistake.
