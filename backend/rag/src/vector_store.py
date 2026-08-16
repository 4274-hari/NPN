"""
Vector Store Module using ChromaDB

Creates and manages three separate ChromaDB collections:
- brand_knowledge
- policy_knowledge
- safety_knowledge

Each collection:
- Stores chunk text, embedding, and metadata
- Uses chunk_id as unique document identifier
- Persists to disk in vector_db/{type}/ directory
- Supports upsert (insert or update)
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings


class ChromaVectorStore:
    """
    ChromaDB wrapper for managing RAG vector databases.
    """
    
    def __init__(self, db_root: Path):
        """
        Initialize ChromaDB client with persistent storage.
        
        Args:
            db_root: Root path for vector_db directory (e.g., RAG/vector_db/)
        """
        self.db_root = Path(db_root)
        self.db_root.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB with persistent storage
        self.client = chromadb.PersistentClient(
            path=str(self.db_root)
        )
        
        # Get or create collections
        self.collections = {
            'brand': self._get_or_create_collection('brand_knowledge'),
            'policy': self._get_or_create_collection('policy_knowledge'),
            'safety': self._get_or_create_collection('safety_knowledge'),
        }
        
        print(f"✓ ChromaDB initialized at: {self.db_root}")
    
    def _get_or_create_collection(self, collection_name: str):
        """
        Get or create a ChromaDB collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            ChromaDB collection object
        """
        # Collections use 'l2' distance metric (Euclidean)
        return self.client.get_or_create_collection(
            name=collection_name,
            metadata={'hnsw:space': 'l2'}
        )
    
    def upsert_chunks(self, rag_type: str, chunks: List[Dict[str, Any]]) -> None:
        """
        Insert or update chunks in the appropriate collection.
        
        Uses chunk_id as unique identifier, so running multiple times
        with the same chunks won't create duplicates.
        
        Args:
            rag_type: One of 'brand', 'policy', 'safety'
            chunks: List of chunk dicts with keys:
                    'text', 'embedding', 'chunk_id', 'source', etc.
        """
        if rag_type not in self.collections:
            raise ValueError(f"Unknown RAG type: {rag_type}")
        
        if not chunks:
            print(f"⚠️  No chunks to upsert for {rag_type.upper()}")
            return
        
        collection = self.collections[rag_type]
        
        # Prepare data for ChromaDB
        ids = []
        embeddings = []
        documents = []
        metadatas = []
        
        for chunk in chunks:
            ids.append(chunk['chunk_id'])
            embeddings.append(chunk['embedding'].tolist())  # Convert numpy to list
            documents.append(chunk['text'])
            
            # Create metadata dict (exclude 'text' and 'embedding')
            metadata = {
                k: v for k, v in chunk.items()
                if k not in ['text', 'embedding']
            }
            metadatas.append(metadata)
        
        # Upsert to collection (insert or update if chunk_id already exists)
        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )
        
        print(f"✓ Upserted {len(chunks)} chunks to {rag_type.upper()} collection")
    
    def query(
        self,
        rag_type: str,
        query_embedding: List[float],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Query a collection using an embedding vector.
        
        Args:
            rag_type: One of 'brand', 'policy', 'safety'
            query_embedding: Embedding vector (list or numpy array)
            top_k: Number of results to return
            
        Returns:
            List of result dicts with keys:
            - text: Chunk content
            - metadata: Chunk metadata (source, category, etc.)
            - distance: L2 distance (lower is more similar)
        """
        if rag_type not in self.collections:
            raise ValueError(f"Unknown RAG type: {rag_type}")
        
        collection = self.collections[rag_type]
        
        # Convert to list if numpy array
        if hasattr(query_embedding, 'tolist'):
            query_embedding = query_embedding.tolist()
        
        # Query the collection
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=['documents', 'distances', 'metadatas']
        )
        
        # Parse results into list of dicts
        output = []
        
        if results['documents'] and len(results['documents']) > 0:
            for idx in range(len(results['documents'][0])):
                result = {
                    'text': results['documents'][0][idx],
                    'metadata': results['metadatas'][0][idx],
                    'distance': float(results['distances'][0][idx]),
                }
                output.append(result)
        
        return output
    
    def get_collection_stats(self, rag_type: str) -> Dict[str, Any]:
        """
        Get statistics for a collection.
        
        Args:
            rag_type: One of 'brand', 'policy', 'safety'
            
        Returns:
            Dict with 'count' key (number of chunks in collection)
        """
        if rag_type not in self.collections:
            raise ValueError(f"Unknown RAG type: {rag_type}")
        
        collection = self.collections[rag_type]
        return {'count': collection.count()}
    
    def print_all_stats(self) -> None:
        """
        Print statistics for all collections.
        """
        print("\n" + "="*50)
        print("VECTOR DATABASE STATISTICS")
        print("="*50)
        
        total = 0
        for rag_type in ['brand', 'policy', 'safety']:
            stats = self.get_collection_stats(rag_type)
            count = stats['count']
            total += count
            print(f"{rag_type.upper():8s}: {count:6d} chunks")
        
        print("-"*50)
        print(f"TOTAL:   {total:6d} chunks")
        print("="*50 + "\n")


def main():
    """
    Demo: Initialize vector store (empty).
    """
    from pathlib import Path
    
    project_root = Path(__file__).parent.parent
    db_root = project_root / 'vector_db'
    
    print("Initializing ChromaDB vector store...")
    vs = ChromaVectorStore(db_root)
    
    print("\nCollection statistics:")
    vs.print_all_stats()


if __name__ == '__main__':
    main()
