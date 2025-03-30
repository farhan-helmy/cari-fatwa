from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel
import os
import chromadb
from openai import OpenAI
from typing import List, Optional
import time
from contextlib import asynccontextmanager

# Environment variables with defaults for development
API_KEY = os.getenv("API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")
DB_PATH = os.getenv("DB_PATH", "/app/chroma_db")
RATE_LIMIT = os.getenv("RATE_LIMIT")

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Lifespan context manager for app startup/shutdown


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize clients
    app.openai_client = OpenAI(api_key=OPENAI_API_KEY)
    app.chroma_client = chromadb.PersistentClient(path=DB_PATH)
    try:
        app.collection = app.chroma_client.get_collection(COLLECTION_NAME)
        print(f"Connected to collection: {COLLECTION_NAME}")
    except Exception as e:
        print(f"Error connecting to collection: {e}")
        raise

    yield

    # Shutdown: cleanup if needed
    # No specific cleanup required

# Initialize API
app = FastAPI(
    title="Fatwa Search API",
    description="API for searching fatwas using vector embeddings",
    version="1.0.0",
    lifespan=lifespan
)

# Register rate limit error handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
api_key_header = APIKeyHeader(name="X-API-Key")

# Models


class QueryRequest(BaseModel):
    query: str
    limit: Optional[int] = 3


class FatwaResult(BaseModel):
    title: str
    url: str
    score: Optional[float] = None


class QueryResponse(BaseModel):
    results: List[FatwaResult]
    query: str
    processing_time: float

# Dependency for API key validation


async def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    return api_key


@app.get("/", dependencies=[Depends(verify_api_key)])
def root():
    return {"message": "Fatwa Search API is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/search", response_model=QueryResponse, dependencies=[Depends(verify_api_key)])
@limiter.limit(RATE_LIMIT)
async def search_fatwas(request: Request, query_request: QueryRequest):
    start_time = time.time()

    try:
        # Generate embedding for the query
        query_embedding = app.openai_client.embeddings.create(
            model="text-embedding-ada-002",
            input=[query_request.query]
        ).data[0].embedding

        # Query the collection
        results = app.collection.query(
            query_embeddings=[query_embedding],
            n_results=query_request.limit,
            include=["metadatas", "distances"]
        )

        # Format results
        fatwa_results = []
        for i, (metadata, distance) in enumerate(zip(results["metadatas"][0], results["distances"][0])):
            fatwa_results.append(
                FatwaResult(
                    title=metadata['title'],
                    url=metadata['url'],
                    score=1.0 - distance  # Convert distance to similarity score
                )
            )

        processing_time = time.time() - start_time

        return QueryResponse(
            results=fatwa_results,
            query=query_request.query,
            processing_time=processing_time
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing query: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
