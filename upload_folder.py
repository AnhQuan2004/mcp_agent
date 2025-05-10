import os
import argparse
import asyncio
from pathlib import Path
import uuid
from datetime import datetime

import PyPDF2
from sentence_transformers import SentenceTransformer
from app.services.document_service import DocumentService
from app.services.text_service import TextService
from app.services.qdrant_service import QdrantService
from app.config.settings import MODEL_NAME

# Initialize services
document_service = DocumentService()
text_service = TextService()
qdrant_service = QdrantService()

async def process_pdf_file(file_path, call_name=None):
    """Process a single PDF file and upload to Qdrant"""
    try:
        file_name = os.path.basename(file_path)
        print(f"Processing {file_name}...")
        
        # Use file name as call_name if not provided
        if not call_name:
            call_name = os.path.splitext(file_name)[0]
        
        # Create a virtual document URL based on filename
        virtual_url = f"file://{file_name}"
        
        # Check if a document with this name already exists
        existing_doc_id = qdrant_service.get_existing_doc_id(virtual_url)
        
        # Generate a unique document ID (reuse if updating)
        doc_id = existing_doc_id if existing_doc_id else str(uuid.uuid4())
        current_date = datetime.now().isoformat()
        
        # If updating, delete existing chunks first
        if existing_doc_id:
            qdrant_service.delete_document_chunks(doc_id)
            print(f"Updating existing document: {file_name}")
        else:
            print(f"Creating new document: {file_name}")
        
        # Extract text from PDF
        with open(file_path, 'rb') as f:
            text = document_service.extract_text_from_pdf(f)
        
        # Split text into chunks and generate embeddings
        chunks = text_service.chunk_text(text)
        
        if not chunks:
            print(f"Warning: No text content extracted from {file_name}")
            return
        
        print(f"Extracted {len(chunks)} chunks from {file_name}")
        embeddings = text_service.generate_embeddings(chunks)
        
        # Prepare points for Qdrant
        points = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            points.append(
                {
                    "id": str(uuid.uuid4()),
                    "vector": embedding,
                    "payload": {
                        "text": chunk,
                        "url": virtual_url,
                        "call_name": call_name,
                        "doc_id": doc_id,
                        "chunk_id": i,
                        "date": current_date,
                        "total_chunks": len(chunks),
                        "file_name": file_name
                    }
                }
            )
        
        # Store in Qdrant
        qdrant_service.upsert_points(points)
        
        print(f"Successfully {'updated' if existing_doc_id else 'embedded'} {file_name} with {len(chunks)} chunks")
        return {
            "file_name": file_name,
            "call_name": call_name,
            "doc_id": doc_id,
            "chunks": len(chunks)
        }
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")
        return None

async def process_folder(folder_path, prefix=None):
    """Process all PDF files in a folder"""
    if not os.path.isdir(folder_path):
        print(f"Error: {folder_path} is not a valid directory")
        return
    
    folder = Path(folder_path)
    pdf_files = list(folder.glob("**/*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in {folder_path}")
        return
    
    print(f"Found {len(pdf_files)} PDF files in {folder_path}")
    
    results = []
    for pdf_file in pdf_files:
        # Use prefix if provided
        if prefix:
            call_name = f"{prefix} - {pdf_file.stem}"
        else:
            call_name = pdf_file.stem
            
        result = await process_pdf_file(str(pdf_file), call_name)
        if result:
            results.append(result)
    
    print(f"Successfully processed {len(results)} out of {len(pdf_files)} files")
    return results

def parse_arguments():
    parser = argparse.ArgumentParser(description="Upload folder of PDFs to Qdrant")
    parser.add_argument("folder", type=str, help="Path to folder containing PDF files")
    parser.add_argument("--prefix", type=str, help="Prefix to add to document names (optional)")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    asyncio.run(process_folder(args.folder, args.prefix)) 