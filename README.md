🧠 SuiAgentic

SuiAgentic is a FastAPI-based application for document embedding and semantic retrieval, powered by the Qdrant vector database. It enables you to convert documents (from URLs or local files) into embeddings, store them efficiently, and retrieve relevant content using natural language queries. It is designed to support AI-enhanced tools like Cursor, Copilot, Claude, and other MCP-compatible clients.

💡 Why SuiAgentic?
Many organizations need to integrate context from internal documents (e.g., PRDs, design specs, wikis) into tools used by developers and knowledge workers. However, consolidating documents from various sources into a centralized, searchable knowledge base is complex and fragmented.

SuiAgentic solves this by providing a centralized context server that ingests, chunks, embeds, and indexes your content—making it available via a simple REST API and web interface. It also supports being used as an MCP server for AI agents.

🚀 Key Features
Document Embedding: Extracts content from URLs (with or without authentication), splits it into chunks, generates embeddings, and stores them in Qdrant.

Semantic Search: Query your knowledge base with natural language and retrieve relevant chunks or documents.

Web UI: Easy-to-use web interface for embedding and searching.

REST API: Fully accessible via HTTP endpoints for automation or integration.

MCP Server Ready: Use it with MCP-compatible clients like Cursor, Copilot, Claude, etc.

Authentication Support: Supports Basic Auth and Bearer Token for protected documents.

⚙️ Quick Start

1. Clone the Repository

```bash
git clone https://github.com/AnhQuan2004/mcp_agent.git
cd mcp_agent
```

2. Set up Python Environment

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

3. Install Dependencies

```bash
pip install -r requirements.txt
```

4. Create .env file (or use the provided .env.example)

```
QDRANT_URL=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=documents
```

5. Start Qdrant (Vector DB)

Using Docker:

```bash
docker run -p 6333:6333 qdrant/qdrant
```

Or using the helper script:

```bash
./runqdrant.sh
```

6. Run the Agentic App

```bash
uvicorn app.main:app --reload
# or:
python run.py
```

Visit http://localhost:8000

🌐 Web Interface & API

Web UI:

- / — Home
- /embed — Embed documents via UI
- /retrieve — Semantic search UI

🔍 POST /retrieve

```json
{
  "query": "What is the architecture of Sui?",
  "top_k": 5,
  "group_by_doc": true
}
```

🌍 Embedding from URLs

Public URLs:

- Just provide the URL via the API or UI — no auth needed.

🤖 Using as an MCP Server

To use sui as an MCP server:

```json
{
  "mcpServers": {
    "suiAgentic": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

# Document Upload Tools

This directory contains tools to bulk upload documents to your SuiAgentic Qdrant database.

## Available Tools

1. `upload_folder.py` - A simple script to upload PDF files from a folder
2. `upload_documents.py` - An advanced script to upload PDF, DOCX, and TXT files with more options

## Prerequisites

- Python 3.8+
- SuiAgentic application installed and configured
- Qdrant server running locally or accessible via network
- Required dependencies installed (PyPDF2, python-docx)

## Basic Usage

### Upload PDF Files from a Folder

```bash
# Upload all PDFs from a folder
python upload_folder.py /path/to/pdf/folder

# Upload with a prefix (useful for categorizing documents)
python upload_folder.py /path/to/pdf/folder --prefix "Research Papers"
```

### Advanced Document Upload

```bash
# Upload all supported documents from a folder and subfolders
python upload_documents.py /path/to/documents --recursive

# Add metadata tags to all documents
python upload_documents.py /path/to/documents --tag category=research --tag project=alpha

# Specify collection name (if not using default)
python upload_documents.py /path/to/documents --collection my_collection

# Complete example with all options
python upload_documents.py /path/to/documents --recursive --prefix "Project X" --tag department=marketing --tag status=final
```

## What These Tools Do

1. Find supported documents in the specified folder
2. Extract text content from each document
3. Split text into manageable chunks
4. Generate 3072-dimensional embeddings for each chunk
5. Store chunks and embeddings in Qdrant
6. Track metadata for each document

## Command-line Arguments

### upload_folder.py

- `folder` - Path to the folder containing PDF files
- `--prefix` - Prefix to add to document names

### upload_documents.py

- `folder` - Path to the folder containing documents
- `--prefix` - Prefix to add to document names
- `--recursive` - Search for files recursively in subfolders
- `--collection` - Name of the Qdrant collection to use
- `--tag` - Add metadata tags to documents (can be used multiple times: `--tag key=value`)

## Examples

### Organize documents by project

```bash
python upload_documents.py /path/to/projects/project1 --recursive --prefix "Project 1" --tag project=alpha
python upload_documents.py /path/to/projects/project2 --recursive --prefix "Project 2" --tag project=beta
```

### Categorize documents

```bash
python upload_documents.py /path/to/contracts --prefix "Legal" --tag department=legal --tag confidential=true
python upload_documents.py /path/to/manuals --prefix "Technical" --tag department=engineering
```

## Troubleshooting

- If you encounter memory errors with large documents, try breaking them into smaller files
- For large collections of documents, consider processing in smaller batches
- Check the log output for any errors during processing

🪪 License

Licensed under the Apache License 2.0.
