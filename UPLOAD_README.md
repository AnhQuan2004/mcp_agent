# Document Upload Tools for ContextMore

This directory contains tools to bulk upload documents to your ContextMore Qdrant database.

## Available Tools

1. `upload_folder.py` - A simple script to upload PDF files from a folder
2. `upload_documents.py` - An advanced script to upload PDF, DOCX, and TXT files with more options

## Prerequisites

- Python 3.8+
- ContextMore application installed and configured
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
