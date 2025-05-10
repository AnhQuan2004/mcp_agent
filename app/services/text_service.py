import requests
import numpy as np
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
from semantic_text_splitter import TextSplitter
from app.config.settings import MODEL_NAME, VECTOR_SIZE
from fastapi import HTTPException
from typing import List, Optional
from app.models.schemas import AuthHeaders, BasicAuth

class TextService:
    def __init__(self):
        self.model = SentenceTransformer(MODEL_NAME)
        self.splitter = TextSplitter(3000)  # Larger chunk size for better context
        self.chunk_size = 300  # Increased number of words per chunk for better context

    def extract_text_from_url(self, url: str, auth_headers: Optional[AuthHeaders] = None, basic_auth: Optional[BasicAuth] = None) -> str:
        """
        Extract text content from a URL with optional authentication
        """
        try:
            # Prepare request parameters
            request_kwargs = {
                'url': url,
                'headers': {},
                'auth': None,
                'timeout': 30
            }

            # Add custom headers if provided
            if auth_headers:
                request_kwargs['headers'].update(auth_headers.headers)

            # Add basic auth if provided
            if basic_auth:
                request_kwargs['auth'] = (basic_auth.username, basic_auth.password)

            # Make the request
            response = requests.get(**request_kwargs)
            response.raise_for_status()

            # Parse HTML content
            soup = BeautifulSoup(response.text, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Get text content
            text = soup.get_text()

            # Clean up text: remove extra whitespace and empty lines
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)

            return text

        except requests.RequestException as e:
            raise ValueError(f"Error fetching URL: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error processing text: {str(e)}")

    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks of approximately chunk_size words
        """
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), self.chunk_size):
            chunk = ' '.join(words[i:i + self.chunk_size])
            if chunk:  # Only add non-empty chunks
                chunks.append(chunk)
        
        return chunks

    def expand_embedding_dimensions(self, embedding: List[float], target_size: int) -> List[float]:
        """
        Expand embedding to the target size
        
        Strategy:
        1. Repeat the embedding until we're close to the target size
        2. If needed, pad with zeros at the end to exactly match the target size
        """
        original_size = len(embedding)
        
        # Calculate how many times to repeat the original embedding
        repeat_times = target_size // original_size
        
        # Repeat the embedding
        expanded = embedding * repeat_times
        
        # Calculate how many elements are still needed
        remaining = target_size - len(expanded)
        
        # Add any remaining elements by padding with zeros
        if remaining > 0:
            expanded.extend([0.0] * remaining)
            
        return expanded

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of text chunks and expand to VECTOR_SIZE
        """
        try:
            # Generate embeddings with the model's native size
            model_embeddings = self.model.encode(texts)
            
            # Convert to list for processing
            embeddings_list = model_embeddings.tolist()
            
            # Get the actual output dimension
            actual_size = len(embeddings_list[0]) if embeddings_list else 0
            
            # If the model's output doesn't match our target size, expand the dimensions
            if actual_size != VECTOR_SIZE:
                print(f"Expanding embeddings from {actual_size} to {VECTOR_SIZE} dimensions")
                expanded_embeddings = []
                
                for embedding in embeddings_list:
                    expanded = self.expand_embedding_dimensions(embedding, VECTOR_SIZE)
                    expanded_embeddings.append(expanded)
                
                return expanded_embeddings
            else:
                return embeddings_list
                
        except Exception as e:
            raise ValueError(f"Error generating embeddings: {str(e)}") 