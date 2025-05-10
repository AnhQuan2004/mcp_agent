import os
import argparse
import asyncio
from pathlib import Path
import uuid
from datetime import datetime
import logging

from app.services.document_service import DocumentService
from app.services.text_service import TextService
from app.services.qdrant_service import QdrantService

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Initialize services
document_service = DocumentService()
text_service = TextService()
qdrant_service = QdrantService()

# Supported file extensions
SUPPORTED_EXTENSIONS = ['.pdf', '.docx', '.txt']

async def process_document(file_path, call_name=None, collection_name=None, metadata=None):
    """Process a single document file and upload to Qdrant"""
    try:
        file_name = os.path.basename(file_path)
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext not in SUPPORTED_EXTENSIONS:
            logger.warning(f"Unsupported file format: {file_ext} for file {file_name}")
            return None
        
        logger.info(f"Processing {file_name}...")
        
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
            logger.info(f"Updating existing document: {file_name}")
        else:
            logger.info(f"Creating new document: {file_name}")
        
        # Extract text based on file extension
        with open(file_path, 'rb') as f:
            text = document_service.extract_text_from_file(f, file_name)
        
        # Split text into chunks and generate embeddings
        chunks = text_service.chunk_text(text)
        
        if not chunks:
            logger.warning(f"No text content extracted from {file_name}")
            return None
        
        logger.info(f"Extracted {len(chunks)} chunks from {file_name}")
        embeddings = text_service.generate_embeddings(chunks)
        
        # Prepare additional metadata if provided
        payload_metadata = {}
        if metadata:
            payload_metadata.update(metadata)
        
        # Prepare points for Qdrant
        points = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            payload = {
                "text": chunk,
                "url": virtual_url,
                "call_name": call_name,
                "doc_id": doc_id,
                "chunk_id": i,
                "date": current_date,
                "total_chunks": len(chunks),
                "file_name": file_name,
                "file_type": file_ext[1:],  # Remove the dot
                **payload_metadata
            }
            
            points.append({
                "id": str(uuid.uuid4()),
                "vector": embedding,
                "payload": payload
            })
        
        # Store in Qdrant
        qdrant_service.upsert_points(points)
        
        logger.info(f"Successfully {'updated' if existing_doc_id else 'embedded'} {file_name} with {len(chunks)} chunks")
        return {
            "file_name": file_name,
            "call_name": call_name,
            "doc_id": doc_id,
            "chunks": len(chunks),
            "file_type": file_ext[1:]
        }
    except Exception as e:
        logger.error(f"Error processing {file_path}: {str(e)}")
        return None

async def process_folder(folder_path, prefix=None, recursive=True, metadata=None, collection_name=None):
    """Process all supported document files in a folder"""
    if not os.path.isdir(folder_path):
        logger.error(f"Error: {folder_path} is not a valid directory")
        return
    
    folder = Path(folder_path)
    
    # Find all supported files
    all_files = []
    if recursive:
        # Search recursively
        for ext in SUPPORTED_EXTENSIONS:
            all_files.extend(list(folder.glob(f"**/*{ext}")))
    else:
        # Search only in the current folder
        for ext in SUPPORTED_EXTENSIONS:
            all_files.extend(list(folder.glob(f"*{ext}")))
    
    if not all_files:
        logger.warning(f"No supported files found in {folder_path}")
        return []
    
    # Sort files by name for consistent processing
    all_files.sort()
    
    logger.info(f"Found {len(all_files)} supported files in {folder_path}")
    
    # Process files
    results = []
    successful = 0
    failed = 0
    
    for file_path in all_files:
        # Use prefix if provided
        if prefix:
            # Add folder structure to call_name if recursive
            if recursive and folder != file_path.parent:
                relative_path = file_path.parent.relative_to(folder)
                call_name = f"{prefix} - {relative_path} - {file_path.stem}"
            else:
                call_name = f"{prefix} - {file_path.stem}"
        else:
            # Add folder structure to call_name if recursive
            if recursive and folder != file_path.parent:
                relative_path = file_path.parent.relative_to(folder)
                call_name = f"{relative_path} - {file_path.stem}"
            else:
                call_name = file_path.stem
        
        result = await process_document(
            str(file_path), 
            call_name=call_name, 
            collection_name=collection_name,
            metadata=metadata
        )
        
        if result:
            results.append(result)
            successful += 1
        else:
            failed += 1
    
    logger.info(f"Processing complete: {successful} successful, {failed} failed")
    return results

def parse_arguments():
    parser = argparse.ArgumentParser(description="Upload documents to Qdrant")
    parser.add_argument("folder", type=str, help="Path to folder containing documents")
    parser.add_argument("--prefix", type=str, help="Prefix to add to document names (optional)")
    parser.add_argument("--recursive", action="store_true", help="Search for files recursively in subfolders")
    parser.add_argument("--collection", type=str, help="Name of the Qdrant collection to use (uses default from settings if not specified)")
    parser.add_argument("--tag", action="append", help="Add metadata tags to documents (can be used multiple times: --tag key=value)")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    
    # Process tags if provided
    metadata = {}
    if args.tag:
        for tag in args.tag:
            if '=' in tag:
                key, value = tag.split('=', 1)
                metadata[key.strip()] = value.strip()
    
    asyncio.run(process_folder(
        args.folder, 
        prefix=args.prefix, 
        recursive=args.recursive, 
        metadata=metadata, 
        collection_name=args.collection
    )) 