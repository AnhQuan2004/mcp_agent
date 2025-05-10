from fastapi import FastAPI, Request, HTTPException, UploadFile, Form, File
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
import uuid
from typing import List, Dict, Any, Optional

from app.models.schemas import URLInput, QueryInput, FileUploadResponse
from app.services.qdrant_service import QdrantService
from app.services.text_service import TextService
from app.services.document_service import DocumentService
from fastapi_mcp import FastApiMCP

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize templates
templates = Jinja2Templates(directory="templates")

# Initialize services
qdrant_service = QdrantService()
text_service = TextService()
document_service = DocumentService()

@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "year": datetime.now().year
    })

@app.get("/embed")
async def get_embed_page(request: Request):
    return templates.TemplateResponse("embed.html", {
        "request": request,
        "year": datetime.now().year
    })

@app.get("/retrieve")
async def get_retrieve_page(request: Request):
    return templates.TemplateResponse("retrieve.html", {
        "request": request,
        "year": datetime.now().year
    })

@app.post("/embed", operation_id="embed_document")
async def embed_document(url_input: URLInput):
    # Check if URL already exists
    existing_doc_id = qdrant_service.get_existing_doc_id(url_input.url)
    
    try:
        # Extract and process text with authentication if provided
        text = text_service.extract_text_from_url(
            url=str(url_input.url),
            auth_headers=url_input.auth_headers,
            basic_auth=url_input.basic_auth
        )
        chunks = text_service.chunk_text(text)
        embeddings = text_service.generate_embeddings(chunks)
        
        # Generate a unique document ID (reuse if updating)
        doc_id = existing_doc_id if existing_doc_id else str(uuid.uuid4())
        current_date = datetime.now().isoformat()
        
        # If updating, delete existing chunks first
        if existing_doc_id:
            qdrant_service.delete_document_chunks(doc_id)
        
        # Prepare points for Qdrant
        points = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            points.append(
                {
                    "id": str(uuid.uuid4()),
                    "vector": embedding,
                    "payload": {
                        "text": chunk,
                        "url": str(url_input.url),
                        "call_name": url_input.call_name,
                        "doc_id": doc_id,
                        "chunk_id": i,
                        "date": current_date,
                        "total_chunks": len(chunks)
                    }
                }
            )
        
        # Store in Qdrant
        qdrant_service.upsert_points(points)
        
        return {
            "message": f"Successfully {'updated' if existing_doc_id else 'embedded'} {len(chunks)} chunks from {url_input.url}",
            "doc_id": doc_id,
            "call_name": url_input.call_name,
            "date": current_date,
            "is_update": existing_doc_id is not None
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/upload-document", response_model=FileUploadResponse, operation_id="upload_document")
async def upload_document(
    file: UploadFile = File(...),
    call_name: str = Form(...)
):
    try:
        # Check file extension
        file_extension = file.filename.split('.')[-1].lower()
        if file_extension not in ['pdf', 'docx', 'txt']:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file format: .{file_extension}. Supported formats: pdf, docx, txt"
            )
        
        # Generate a document ID
        doc_id = str(uuid.uuid4())
        current_date = datetime.now().isoformat()
        
        # Reset file pointer to the beginning
        await file.seek(0)
        
        # Extract text from the file
        file_content = await file.read()
        # Reset file position for reading again
        await file.seek(0)
        
        # Create a virtual document URL based on filename
        virtual_url = f"file://{file.filename}"
        
        # Check if a document with this name already exists
        existing_doc_id = qdrant_service.get_existing_doc_id(virtual_url)
        if existing_doc_id:
            doc_id = existing_doc_id
            qdrant_service.delete_document_chunks(doc_id)
        
        # Extract text from the file
        text = document_service.extract_text_from_file(file.file, file.filename)
        
        # Process text similar to URL embedding
        chunks = text_service.chunk_text(text)
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
                        "file_name": file.filename
                    }
                }
            )
        
        # Store in Qdrant
        qdrant_service.upsert_points(points)
        
        return FileUploadResponse(
            message=f"Successfully {'updated' if existing_doc_id else 'embedded'} {len(chunks)} chunks from {file.filename}",
            doc_id=doc_id,
            call_name=call_name,
            date=current_date,
            is_update=existing_doc_id is not None,
            file_name=file.filename
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/retrieve" , operation_id="retrieve_documents")
async def retrieve_documents(query_input: QueryInput):
    # Generate embedding for the query
    query_embedding = text_service.generate_embeddings([query_input.query])[0]
    
    # Search in Qdrant
    search_results = qdrant_service.search_points(
        query_vector=query_embedding,
        limit=query_input.top_k * 4
    )
    
    if query_input.group_by_doc:
        # Group results by document
        doc_results = {}
        for hit in search_results.points:
            doc_id = hit.payload["doc_id"]
            if doc_id not in doc_results:
                doc_results[doc_id] = {
                    "doc_id": doc_id,
                    "call_name": hit.payload["call_name"],
                    "url": hit.payload["url"],
                    "date": hit.payload["date"],
                    "chunks": [],
                    "total_chunks": hit.payload["total_chunks"],
                    "avg_score": 0,
                    "file_name": hit.payload.get("file_name", None)
                }
            
            doc_results[doc_id]["chunks"].append({
                "text": hit.payload["text"],
                "chunk_id": hit.payload["chunk_id"],
                "score": hit.score
            })
            doc_results[doc_id]["avg_score"] += hit.score
        
        # Calculate average scores and sort documents
        for doc_id in doc_results:
            doc_results[doc_id]["avg_score"] /= len(doc_results[doc_id]["chunks"])
            doc_results[doc_id]["chunks"].sort(key=lambda x: x["chunk_id"])
        
        results = list(doc_results.values())
        results.sort(key=lambda x: x["avg_score"], reverse=True)
        return {"results": results}
    else:
        # Return individual chunks without grouping
        results = []
        for hit in search_results.points:
            results.append({
                "text": hit.payload["text"],
                "url": hit.payload["url"],
                "call_name": hit.payload["call_name"],
                "doc_id": hit.payload["doc_id"],
                "chunk_id": hit.payload["chunk_id"],
                "date": hit.payload["date"],
                "score": hit.score,
                "file_name": hit.payload.get("file_name", None)
            })
        
        results.sort(key=lambda x: x["score"], reverse=True)
        return {"results": results}

# Mount MCP routes
mcp = FastApiMCP(
    app,
    name="contextmore api mcp",
    description="ContextMore is a tool that allows you to embed documents and search them using a vector database. It is designed to be used in conjunction with the ContextMore MCP server.",
    include_operations=["embed_document", "upload_document", "retrieve_documents"],
    include_tags=["embed", "retrieve", "contextmore"]
)
mcp.mount() 