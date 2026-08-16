"""
Main Indexing Pipeline

Orchestrates the complete RAG ingestion workflow:
Load → Chunk → Embed → Store

This is the entry point to build or update all three vector databases.
"""

from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from loader import load_all_documents
from chunker import chunk_documents
from embedder import embed_chunks_for_storage
from vector_store import store_chunks_in_vectors


def build_rag_index(base_path: Path):
    """
    Build or update the complete RAG index.

    Args:
        base_path: Root path of the RAG project
    """
    print("\n" + "=" * 50)
    print("RAG INDEXING PIPELINE")
    print("=" * 50 + "\n")

    try:
        # Step 1: Load documents
        print("STEP 1: LOADING DOCUMENTS")
        print("-" * 50)
        documents = load_all_documents(base_path)

        if not documents:
            print("❌ No documents loaded. Aborting.")
            return

        # Step 2: Chunk documents
        print("\nSTEP 2: CHUNKING DOCUMENTS")
        print("-" * 50)
        chunks = chunk_documents(documents)

        if not chunks:
            print("❌ No chunks created. Aborting.")
            return

        # Step 3: Generate embeddings
        print("\nSTEP 3: GENERATING EMBEDDINGS")
        print("-" * 50)
        chunks = embed_chunks_for_storage(chunks)

        # Step 4: Store in vector database
        print("\nSTEP 4: STORING IN VECTOR DATABASE")
        print("-" * 50)
        inserted = store_chunks_in_vectors(chunks, base_path)

        # Summary
        print("\n" + "=" * 50)
        print("✅ INDEXING COMPLETE")
        print("=" * 50)
        print(f"Brand: {inserted['brand']} chunks")
        print(f"Policy: {inserted['policy']} chunks")
        print(f"Safety: {inserted['safety']} chunks")
        print(f"TOTAL: {sum(inserted.values())} chunks\n")

    except Exception as e:
        print(f"\n❌ Indexing failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Determine base path (parent of src/)
    base_path = Path(__file__).parent.parent

    build_rag_index(base_path)
