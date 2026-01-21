import os
import chromadb

def get_chroma_client():
    """
    Creates and returns a Chroma client.
    Supports:
      - Chroma Cloud (if CHROMA_API_KEY etc. exist)
      - Local persistent Chroma (if CHROMA_PATH exists)
    """
    chroma_path = os.getenv("CHROMA_PATH")

    chroma_api_key = os.getenv("CHROMA_API_KEY")
    chroma_tenant = os.getenv("CHROMA_TENANT")
    chroma_database = os.getenv("CHROMA_DATABASE")

    # Connect to Chroma Cloud when credentials are present
    if chroma_api_key and chroma_tenant and chroma_database:
        print("Using Chroma Cloud")
        return chromadb.CloudClient(
            tenant=chroma_tenant,
            database=chroma_database,
            api_key=chroma_api_key,
        )

    # Fall back to local persistent Chroma
    if chroma_path:
        print(f"Using local persistent Chroma at {chroma_path}")
        return chromadb.PersistentClient(path=chroma_path)

    # Fallback for in-memory Chroma (not persistent)
    print("Using in-memory Chroma (not persistent)")
    return chromadb.Client()


def get_chroma_collection():
    """
    Returns the Chroma collection handle.
    """
    collection_name = os.getenv("CHROMA_COLLECTION_NAME", "policy_collection")
    client = get_chroma_client()
    return client.get_or_create_collection(name=collection_name)