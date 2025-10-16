import os
import json
import numpy as np
import time
from pinecone.grpc import PineconeGRPC as Pinecone
from pinecone import ServerlessSpec
from pyairtable import Api
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any

# The embedding model to use. 'all-MiniLM-L12-v2' is fast and effective.
EMBEDDING_MODEL_NAME = 'all-MiniLM-L12-v2'
RECORD_LIMIT = 5 # Limit for demonstration purposes
INDEX_NAME = "cosmos-airtable-index"

def setup_airtable_api() -> Api:
    """Initializes and returns the pyAirtable API client."""
    api_key = os.environ.get("AIRTABLE_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "AIRTABLE_API_KEY environment variable not set. "
            "Please configure your Airtable API key."
        )
    return Api(api_key)

def fetch_airtable_data(api: Api, base_id: str, table_name: str) -> List[Dict[str, Any]]:
    """
    Fetches records from the specified Airtable table.

    Args:
        api: The initialized pyAirtable API instance.
        base_id: The ID of the Airtable Base.
        table_name: The name of the Table to fetch data from.

    Returns:
        A list of Airtable record dictionaries.
    """
    print(f"1. Connecting to Airtable Base '{base_id}', Table '{table_name}'...")
    try:
        table = api.table(base_id, table_name)
        # Fetch a limited number of records for the demo
        # records = table.all(max_records=RECORD_LIMIT)
        records = table.all()
        print(f"   -> Successfully fetched {len(records)} records.")
        return records
    except Exception as e:
        print(f"   -> ERROR fetching data: {e}")
        print("   -> Check your BASE_ID and TABLE_NAME for correctness.")
        return []


def prepare_texts_for_encoding(records: List[Dict[str, Any]]) -> List[str]:
    """
    Converts the structured Airtable records into clean, continuous text strings.

    Vector models work best when given coherent sentences or paragraphs.
    This function concatenates all field values into a single text.

    Args:
        records: List of Airtable records.

    Returns:
        A list of clean text strings, one for each record.
    """
    prepared_texts = []
    print("\n2. Preparing text strings from record fields...")

    for record in records:
        text_parts = []
        # We only care about the 'fields' part of the record
        fields = record.get('fields', {})

        for field_name, value in fields.items():
            # Skip fields that don't convert well (like attachments or lists of links)
            # You might need to customize this based on your specific table schema
            if isinstance(value, (str, int, float)):
                text_parts.append(f"{field_name}: {value}")
            elif isinstance(value, list) and all(isinstance(i, str) for i in value):
                text_parts.append(f"{field_name}: {', '.join(value)}")

        # Join all parts into one coherent string
        full_text = ". ".join(text_parts).strip()
        prepared_texts.append(full_text)

    print(f"   -> Prepared {len(prepared_texts)} text strings for encoding.")
    return prepared_texts


def generate_vectors(texts: List[str]) -> np.ndarray:
    """
    Generates high-dimensional vector embeddings for the provided texts.

    Args:
        texts: A list of text strings.

    Returns:
        A NumPy array of the generated vectors.
    """
    print(f"\n3. Initializing Sentence Transformer model: {EMBEDDING_MODEL_NAME}...")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    print("4. Generating vector embeddings (This may take a moment)...")
    # The 'encode' method is the core of the vectorization process
    vectors = model.encode(texts, convert_to_numpy=True)
    print(f"   -> Generated {vectors.shape[0]} vectors of dimension {vectors.shape[1]}.")
    return vectors


def create_vector_db_payload(records: List[Dict[str, Any]], texts: List[str], vectors: np.ndarray) -> List[Dict[str, Any]]:
    """Combines original data, prepared text, and vectors into a final payload structure."""
    payload = []
    for i, record in enumerate(records):
        payload.append({
            "airtable_id": record['id'],
            "original_record": record['fields'],
            "searchable_text": texts[i],
            "vector": vectors[i].tolist() # Convert numpy array to list for JSON/DB storage
        })
    return payload


def insert_into_vector_db(payload: List[Dict[str, Any]]):
    PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
    pc = Pinecone(api_key=PINECONE_API_KEY)

    if not pc.has_index(INDEX_NAME):
        pc.create_index(
            name=INDEX_NAME,
            vector_type="dense",
            dimension=384,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            ),
        )
    
    # Target the index
    dense_index = pc.Index(INDEX_NAME)

    # Convert payload to Pinecone format
    pinecone_records = []
    for i, record in enumerate(payload):
        pinecone_record = {
            "id": record["airtable_id"],
            "values": record["vector"],
            "metadata": {
                "airtable_id": record["airtable_id"],
                # "original_record": record["original_record"],
                "searchable_text": record["searchable_text"]
            }
        }
        pinecone_records.append(pinecone_record)

    # Upsert the records into a namespace
    print(f"\n6. Uploading {len(pinecone_records)} records to Pinecone...")
    dense_index.upsert(vectors=pinecone_records, namespace="airtable-namespace")
    print("   -> Records uploaded successfully!")

    # Wait for the upserted vectors to be indexed
    print("   -> Waiting for indexing to complete...")
    time.sleep(10)

    # View stats for the index
    print("\n7. Index Statistics:")
    stats = dense_index.describe_index_stats()
    print(stats)

def main():
    """Main execution function to run the pipeline."""
    try:
        # --- 0. Setup Configuration ---
        BASE_ID = os.environ.get("AIRTABLE_BASE_ID")
        TABLE_NAME = os.environ.get("AIRTABLE_TABLE_NAME")

        if not BASE_ID or not TABLE_NAME:
            print("Please set AIRTABLE_BASE_ID and AIRTABLE_TABLE_NAME environment variables.")
            return

        # --- 1. Fetch Data ---
        api = setup_airtable_api()
        airtable_records = fetch_airtable_data(api, BASE_ID, TABLE_NAME)

        if not airtable_records:
            return

        # --- 2. Prepare Text ---
        prepared_texts = prepare_texts_for_encoding(airtable_records)

        # --- 3. Generate Vectors ---
        vectors = generate_vectors(prepared_texts)

        # --- 4. Create Final Payload ---
        final_payload = create_vector_db_payload(airtable_records, prepared_texts, vectors)

        # --- 5. Output Result ---
        print("\n\n5. Pipeline Complete. Ready for Vector DB Insertion.")
        print("-" * 50)
        print(f"Example of the final structure (Record 1):\n")

        # Use json.dumps for pretty printing the sample record
        print(json.dumps(final_payload[0], indent=2))
        print("-" * 50)
        print(f"\nTotal records processed: {len(final_payload)}")
        print("The 'vector' key contains the high-dimensional embedding (ready for insertion).")

        # --- 6. Insert into Vector DB ---
        insert_into_vector_db(final_payload)

    except EnvironmentError as e:
        print(f"Configuration Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    # Ensure necessary libraries are installed:
    # pip install pyairtable sentence-transformers numpy
    main()
