import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Qdrant configuration
QDRANT_URL = os.getenv("QDRANT_URL", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "contextmore")

# Vector dimensions
# Note: Most sentence transformer models don't output 3072 dimensions by default
# The actual output dimensions might be smaller (usually 768 or 1024)
# To achieve 3072 dimensions, you can use a larger model or potentially
# use techniques like concatenation or dimensionality expansion
VECTOR_SIZE = 3072

# Model configuration
# Using one of the largest sentence-transformer models available
MODEL_NAME = 'sentence-transformers/all-mpnet-base-v2'  # 768 dimensions

# Set this to True to recreate the collection with new vector dimensions
RECREATE_COLLECTION = True 