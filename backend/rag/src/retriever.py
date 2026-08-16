"""
Retrieval Module

Provides separate retrieval functions for each RAG type:
- retrieve_brand(query, top_k=5)
- retrieve_policy(query, top_k=5)
- retrieve_safety(query, top_k=5)

Each function:
1. Encodes query to embedding
2. Searches appropriate vector database
3. Returns top-k results with metadata and scores
"""

from typing import List, Dict, Any
from pathlib import Path
from embedder import Embedder
from vector_store import ChromaVectorStore


class RAGRetriever:
    """
    Unified retriever for all RAG types.
    """
    
    def __init__(self, db_root: Path):
        """
        Initialize retriever with embedder and vector store.
        
        Args:
            db_root: Root path for vector_db directory
        """
        self.embedder = Embedder()
        self.vector_store = ChromaVectorStore(db_root)

    def retrieve_brand(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve from the Brand knowledge base."""
        return self.retrieve(query, 'brand', top_k)

    def retrieve_policy(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve from the Policy knowledge base."""
        return self.retrieve(query, 'policy', top_k)

    def retrieve_safety(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve from the Safety knowledge base."""
        return self.retrieve(query, 'safety', top_k)
    
    def retrieve(
        self,
        query: str,
        rag_type: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant chunks for a query from a specific RAG.
        
        Args:
            query: User query string
            rag_type: One of 'brand', 'policy', 'safety'
            top_k: Number of results to return
            
        Returns:
            List of results with keys:
            - text: Chunk content
            - source: Source filename
            - category: Document category
            - rag_type: Type of RAG
            - similarity: Similarity score (1 / (1 + distance))
            - distance: L2 distance
            - relative_path: Path within project
            - chunk_id: Unique chunk identifier
        """
        if rag_type not in ['brand', 'policy', 'safety']:
            raise ValueError(
                f"Unknown RAG type: {rag_type}. "
                "Must be one of: 'brand', 'policy', 'safety'"
            )
        
        # Encode query
        query_embedding = self.embedder.embed_text(query)
        
        # Query vector store
        raw_results = self.vector_store.query(rag_type, query_embedding, top_k)
        
        # Enrich results with formatted output
        results = []
        for raw_result in raw_results:
            metadata = raw_result['metadata']
            distance = raw_result['distance']
            
            # Convert distance to similarity score (0-1)
            # Lower distance = higher similarity
            similarity = 1 / (1 + distance)
            
            result = {
                'text': raw_result['text'],
                'source': metadata.get('source', 'unknown'),
                'category': metadata.get('category', 'unknown'),
                'rag_type': metadata.get('rag_type', rag_type),
                'relative_path': metadata.get('relative_path', 'unknown'),
                'chunk_id': metadata.get('chunk_id', 'unknown'),
                'similarity': round(similarity, 4),
                'distance': round(distance, 4),
            }
            results.append(result)
        
        return results


# Singleton retriever instance (initialized on first import)
_retriever_instance = None


def _get_retriever(project_root: Path = None) -> RAGRetriever:
    """
    Get or create a singleton RAGRetriever instance.
    
    Args:
        project_root: Project root path (only used on first call)
        
    Returns:
        RAGRetriever instance
    """
    global _retriever_instance
    
    if _retriever_instance is None:
        if project_root is None:
            project_root = Path(__file__).parent.parent
        
        db_root = project_root / 'vector_db'
        _retriever_instance = RAGRetriever(db_root)
    
    return _retriever_instance


def retrieve_brand(
    query: str,
    top_k: int = 5,
    project_root: Path = None
) -> List[Dict[str, Any]]:
    """
    Retrieve from Brand knowledge base.
    
    Args:
        query: User query
        top_k: Number of results
        project_root: Project root (optional)
        
    Returns:
        List of relevant chunks
    """
    retriever = _get_retriever(project_root)
    return retriever.retrieve(query, 'brand', top_k)


def retrieve_policy(
    query: str,
    top_k: int = 5,
    project_root: Path = None
) -> List[Dict[str, Any]]:
    """
    Retrieve from Policy knowledge base.
    
    Args:
        query: User query
        top_k: Number of results
        project_root: Project root (optional)
        
    Returns:
        List of relevant chunks
    """
    retriever = _get_retriever(project_root)
    return retriever.retrieve(query, 'policy', top_k)


def retrieve_safety(
    query: str,
    top_k: int = 5,
    project_root: Path = None
) -> List[Dict[str, Any]]:
    """
    Retrieve from Safety knowledge base.
    
    Args:
        query: User query
        top_k: Number of results
        project_root: Project root (optional)
        
    Returns:
        List of relevant chunks
    """
    retriever = _get_retriever(project_root)
    return retriever.retrieve(query, 'safety', top_k)


def create_retriever(base_path: Path = None) -> RAGRetriever:
    """
    Factory function expected by the project entry points.

    Args:
        base_path: Project root containing the vector_db directory

    Returns:
        Initialized RAGRetriever instance
    """
    if base_path is None:
        base_path = Path(__file__).parent.parent

    base_path = Path(base_path)
    return RAGRetriever(base_path / 'vector_db')


def print_result(result: Dict[str, Any]) -> None:
    """
    Pretty-print a single retrieval result.
    
    Args:
        result: Result dict from retrieve_*() functions
    """
    print("-" * 70)
    print(f"RAG TYPE:    {result['rag_type'].upper()}")
    print(f"SOURCE:      {result['source']}")
    print(f"CATEGORY:    {result['category']}")
    print(f"SIMILARITY:  {result['similarity']:.4f}")
    print(f"CHUNK ID:    {result['chunk_id']}")
    print("-" * 70)
    print(f"TEXT:\n{result['text']}")
    print()


def main():
    """
    Demo: Test retriever with sample queries.
    """
    project_root = Path(__file__).parent.parent
    
    print("Initializing retriever...")
    retriever = _get_retriever(project_root)
    
    # Test queries
    test_queries = {
        'brand': [
            "What plans does Nexora offer?",
            "Why was I charged twice?",
            "My internet connection is not working.",
        ],
        'policy': [
            "Which team handles security issues?",
            "What happens when urgency is high?",
        ],
        'safety': [
            "Can the AI request the customer's password?",
            "What should the AI do with sensitive information?",
        ],
    }
    
    for rag_type, queries in test_queries.items():
        print(f"\n{'='*70}")
        print(f"TESTING {rag_type.upper()} RAG")
        print(f"{'='*70}\n")
        
        for query in queries:
            print(f"Query: {query}\n")
            
            if rag_type == 'brand':
                results = retrieve_brand(query, top_k=2, project_root=project_root)
            elif rag_type == 'policy':
                results = retrieve_policy(query, top_k=2, project_root=project_root)
            else:  # safety
                results = retrieve_safety(query, top_k=2, project_root=project_root)
            
            if results:
                for result in results:
                    print_result(result)
            else:
                print("⚠️  No results found.\n")


if __name__ == '__main__':
    main()
