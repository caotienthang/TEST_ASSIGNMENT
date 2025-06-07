# Medical Dialogue Chatbot (Flask + Qdrant + Ollama)

A context-enhanced chatbot for medical dialogue retrieval and response using:

- Qdrant for vector storage/search  
- SentenceTransformers for embedding  
- Deepseek + Ollama (local LLM inference)  
- Flask REST API

## Features

- Inserts and indexes dialogue data into Qdrant for contextual search.
- Retrieves similar past dialogues to enrich responses.
- Calls Deepseek or other Ollama LLMs to answer user queries.
- Modular, supports both API and script interaction.

## Quickstart

### 1. Prerequisites

- Python 3.10+
- Docker
- Running Qdrant instance (`docker run -p 6333:6333 qdrant/qdrant`)
- Running Ollama instance (`docker run -p 11434:11434 ollama/ollama` and load a model, e.g., `deepseek`)
- (Optional) Your own OpenAI or Gemini API keys if you wish to use those

---

### 2. Clone the Project

```bash
git clone https://github.com/yourorg/your-repo.git
cd your-repo
