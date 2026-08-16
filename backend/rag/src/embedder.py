"""
Embeddings Module

Generates embeddings using sentence-transformers.

Uses: sentence-transformers/all-MiniLM-L6-v2
- Lightweight model suitable for CPU
- ~22M parameters, ~84MB on disk
- 384-dimensional embeddings
- Good performance on semantic similarity tasks

Can be easily swapped for other sentence-transformers models.
"""

from typing import List, Union
import numpy as np
from sentence_transformers import SentenceTransformer


class Embedder:
    """
    Wrapper for sentence-transformers embeddings.
    
    Features:
    - Lazy loads model on first use
    - Caches model instance
    - Batch embedding support
    """
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize embedder (model not loaded until first use).
        
        Args:
            model_name: HuggingFace model identifier
            
        Recommended models for CPU:
        - sentence-transformers/all-MiniLM-L6-v2 (384 dims, ~84MB)
        - sentence-transformers/all-MiniLM-L12-v2 (384 dims, ~133MB)
        - sentence-transformers/paraphrase-MiniLM-L6-v2 (384 dims, ~84MB)
        """
        self.model_name = model_name
        self._model = None
    
    @property
    def model(self) -> SentenceTransformer:
        """
        Lazy-load and cache the embedding model.
        
        Returns:
            Loaded SentenceTransformer model
        """
        if self._model is None:
            print(f"Loading embedding model: {self.model_name}...")
            self._model = SentenceTransformer(self.model_name)
            print(f"✓ Model loaded successfully")
        return self._model
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text string
            
        Returns:
            numpy array of shape (embedding_dim,)
        """
        return self.model.encode(text, convert_to_numpy=True)
    
    def embed_texts(self, texts: List[str], batch_size: int = 32) -> List[np.ndarray]:
        """
        Generate embeddings for multiple texts.
        
        Processes in batches for efficiency.
        
        Args:
            texts: List of text strings
            batch_size: Batch size for processing
            
        Returns:
            List of numpy arrays, one per input text
        """
        if not texts:
            return []
        
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True
        )
        
        return [embeddings[i] for i in range(len(texts))]
    
    def embed_chunks(self, chunks: List[dict], batch_size: int = 32) -> List[dict]:
        """
        Generate embeddings for a list of chunk dictionaries.
        
        Args:
            chunks: List of chunk dicts with 'text' key
            batch_size: Batch size for processing
            
        Returns:
            List of chunk dicts with added 'embedding' key (numpy array)
        """
        if not chunks:
            return []
        
        # Extract text from chunks
        texts = [chunk['text'] for chunk in chunks]
        
        # Embed all texts
        embeddings = self.embed_texts(texts, batch_size=batch_size)
        
        # Add embeddings back to chunks
        for chunk, embedding in zip(chunks, embeddings):
            chunk['embedding'] = embedding
        
        return chunks
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings produced by this model.
        
        Returns:
            Embedding dimension (e.g., 384 for MiniLM)
        """
        # All MiniLM models use 384 dimensions
        # Can verify by encoding a dummy text
        return len(self.embed_text("test"))


def main():
    """
    Demo: Test embedder with sample texts.
    """
    
    # Create embedder
    embedder = Embedder()
    
    # Test single embedding
    print("Testing single embedding...")
    text1 = "What are the plans offered by Nexora?"
    embedding1 = embedder.embed_text(text1)
    print(f"✓ Embedding dimension: {len(embedding1)}")
    print(f"  Text: {text1}")
    print(f"  Embedding shape: {embedding1.shape}")
    
    # Test batch embedding
    print("\nTesting batch embedding...")
    texts = [
        "What is Nexora?",
        "How do I cancel my plan?",
        "Is my account secure?",
    ]
    embeddings = embedder.embed_texts(texts)
    print(f"✓ Generated {len(embeddings)} embeddings")
    for text, emb in zip(texts, embeddings):
        print(f"  {text[:40]:40s} | shape: {emb.shape}")
    
    # Test chunks
    print("\nTesting chunk embedding...")
    chunks = [
        {
            'text': 'Nexora offers mobile and broadband plans.',
            'source': 'plans.md',
            'rag_type': 'brand',
        },
        {
            'text': 'Security is handled by the Security team.',
            'source': 'routing.md',
            'rag_type': 'policy',
        },
    ]
    chunks = embedder.embed_chunks(chunks)
    print(f"✓ Embedded {len(chunks)} chunks")
    for chunk in chunks:
        print(f"  {chunk['source']:20s} | embedding shape: {chunk['embedding'].shape}")


if __name__ == '__main__':
    main()
