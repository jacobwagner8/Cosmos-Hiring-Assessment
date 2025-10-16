import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import uvicorn
import google.generativeai as genai

# Add the current directory to Python path to import our query module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our existing query functions
from query_pinecone_db import embed_query, query_pinecone, setup_pinecone

app = FastAPI(title="Cosmos Nexus API", version="1.0.0")

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request model
class SearchRequest(BaseModel):
    query: str
    top_k: int = 5

# Response model
class SearchResult(BaseModel):
    score: float
    id: str
    metadata: Dict[str, Any]

class SearchResponse(BaseModel):
    results: List[SearchResult]
    query: str
    total_results: int
    ai_response: str

# Global variable to store the Pinecone index
pinecone_index = None
gemini_model = None

def setup_gemini():
    """Initialize Gemini API."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GEMINI_API_KEY environment variable not set. "
            "Please configure your Gemini API key."
        )
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash-lite')
    return model

def generate_ai_response(query: str, search_results: List[SearchResult]) -> str:
    """
    Generate a human-readable response using Gemini based on the query and search results.
    """
    try:
        # Prepare context from search results
        context_parts = []
        for i, result in enumerate(search_results, 1):
            context_parts.append(f"Result {i} (Score: {result.score:.3f}):\n{result.metadata.get('searchable_text', 'No text available')}\n")
        
        context = "\n".join(context_parts)
        
        # Create the prompt for Gemini
        prompt = f"""
You are a helpful assistant that answers questions based on the provided search results from a user information database.

Original Query: {query}

Search Results:
{context}

Please provide a comprehensive, human-readable answer to the original query based on the search results above. 
- Be specific and cite relevant details from the case studies
- If the results don't contain enough information to fully answer the query, mention this
- Keep the response informative but concise
- Use a professional, helpful tone

Answer:
"""
        
        # Generate response using Gemini
        response = gemini_model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        print(f"Error generating AI response: {e}")
        return f"I found {len(search_results)} relevant results, but encountered an error generating a detailed response. Please check the individual results below."

@app.on_event("startup")
async def startup_event():
    """Initialize Pinecone and Gemini connections on startup."""
    global pinecone_index, gemini_model
    try:
        print("Initializing Pinecone connection...")
        pinecone_index = setup_pinecone()
        print("Pinecone connection established successfully!")
        
        print("Initializing Gemini API...")
        gemini_model = setup_gemini()
        print("Gemini API initialized successfully!")
        
    except Exception as e:
        print(f"Failed to initialize services: {e}")
        raise

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Cosmos Nexus API is running!"}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy", 
        "pinecone_connected": pinecone_index is not None,
        "gemini_connected": gemini_model is not None
    }

@app.post("/search", response_model=SearchResponse)
async def search_endpoint(request: SearchRequest):
    """
    Search endpoint that queries Pinecone with the provided query.
    """
    try:
        if not pinecone_index:
            raise HTTPException(status_code=500, detail="Pinecone not initialized")
        
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Generate embedding for the query
        print(f"Processing query: '{request.query}'")
        query_vector = embed_query(request.query)
        
        # Query Pinecone
        results = query_pinecone(
            pinecone_index, 
            query_vector, 
            top_k=request.top_k,
            include_metadata=True
        )
        
        # Convert results to our response format
        search_results = []
        for match in results:
            search_results.append(SearchResult(
                score=float(match.score),
                id=match.id,
                metadata=match.metadata or {}
            ))
        
        # Generate AI response using Gemini
        print(f"Generating AI response for query: '{request.query}'")
        ai_response = generate_ai_response(request.query, search_results)
        
        return SearchResponse(
            results=search_results,
            query=request.query,
            total_results=len(search_results),
            ai_response=ai_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "backend:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )
