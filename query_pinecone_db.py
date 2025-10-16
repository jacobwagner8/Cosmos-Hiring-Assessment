import os
import numpy as np
from pinecone.grpc import PineconeGRPC as Pinecone
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any

# The embedding model to use (must match the ingestion script)
EMBEDDING_MODEL_NAME = 'all-MiniLM-L12-v2'
INDEX_NAME = "cosmos-airtable-index"
NAMESPACE = "airtable-namespace"

def setup_pinecone():
    """Initialize Pinecone client and get the index."""
    api_key = os.environ.get("PINECONE_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "PINECONE_API_KEY environment variable not set. "
            "Please configure your Pinecone API key."
        )
    
    pc = Pinecone(api_key=api_key)
    
    if not pc.has_index(INDEX_NAME):
        raise EnvironmentError(f"Index '{INDEX_NAME}' not found. Please run the ingestion script first.")
    
    return pc.Index(INDEX_NAME)

def embed_query(query: str) -> List[float]:
    """
    Generate vector embedding for the query using the same model as ingestion.
    
    Args:
        query: The search query string.
        
    Returns:
        List of float values representing the query vector.
    """
    print(f"Embedding query: '{query}'")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    vector = model.encode([query], convert_to_numpy=True)[0]
    return vector.tolist()

def query_pinecone(index, query_vector: List[float], top_k: int = 5, include_metadata: bool = True) -> List[Dict[str, Any]]:
    """
    Query the Pinecone index with the embedded query vector.
    
    Args:
        index: Pinecone index object.
        query_vector: The embedded query vector.
        top_k: Number of results to return.
        include_metadata: Whether to include metadata in results.
        
    Returns:
        List of query results with scores and metadata.
    """
    print(f"Querying Pinecone index for top {top_k} results...")
    
    results = index.query(
        vector=query_vector,
        top_k=top_k,
        include_metadata=include_metadata,
        namespace=NAMESPACE
    )
    
    return results.matches

def display_results(results: List[Dict[str, Any]], query: str):
    """
    Display the query results in a formatted way.
    
    Args:
        results: List of query results from Pinecone.
        query: Original query string for context.
    """
    print(f"\n{'='*60}")
    print(f"SEARCH RESULTS for: '{query}'")
    print(f"{'='*60}")
    
    if not results:
        print("No results found.")
        return
    
    for i, match in enumerate(results, 1):
        print(f"\n{i}. Score: {match.score:.4f}")
        print(f"   Airtable ID: {match.id}")
        
        if match.metadata:
            print(f"   Searchable Text: {match.metadata.get('searchable_text', 'N/A')[:200]}...")
            print(f"   Airtable ID (metadata): {match.metadata.get('airtable_id', 'N/A')}")
        
        print("-" * 40)

def interactive_query():
    """
    Interactive query interface for searching the Pinecone index.
    """
    try:
        # Setup
        print("Initializing Pinecone connection...")
        index = setup_pinecone()
        
        # Get index stats
        stats = index.describe_index_stats()
        print(f"Index '{INDEX_NAME}' is ready!")
        print(f"Total vectors: {stats.total_vector_count}")
        print(f"Namespaces: {list(stats.namespaces.keys())}")
        
        print("\n" + "="*60)
        print("Pinecone Query Interface")
        print("="*60)
        print("Enter your search queries (type 'quit' to exit)")
        print("-" * 60)
        
        while True:
            query = input("\nEnter your search query: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if not query:
                print("Please enter a valid query.")
                continue
            
            try:
                # Embed the query
                query_vector = embed_query(query)
                
                # Query Pinecone
                results = query_pinecone(index, query_vector, top_k=5)
                
                # Display results
                display_results(results, query)
                
            except Exception as e:
                print(f"Error processing query: {e}")
                continue
                
    except EnvironmentError as e:
        print(f"Configuration Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def single_query(query: str, top_k: int = 5):
    """
    Perform a single query and return results.
    
    Args:
        query: The search query string.
        top_k: Number of results to return.
        
    Returns:
        List of query results.
    """
    try:
        # Setup
        index = setup_pinecone()
        
        # Embed and query
        query_vector = embed_query(query)
        results = query_pinecone(index, query_vector, top_k=top_k)
        
        # Display results
        display_results(results, query)
        
        return results
        
    except Exception as e:
        print(f"Error: {e}")
        return []

def main():
    """
    Main function - performs a hardcoded query.
    """
    # Hardcoded query - update this as needed
    query = "People who graduated Phi Beta Kappa"
    print(f"Performing query: '{query}'")
    single_query(query)

if __name__ == "__main__":
    # Hardcoded query mode - update the query variable in main() as needed
    main()
