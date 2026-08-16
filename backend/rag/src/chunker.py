"""
Document Chunker

Splits Markdown documents into meaningful chunks based on structure:
- Prefers splitting at Markdown headings
- Uses fallback character-based splitting if no headings found
- Preserves metadata from original documents
- Generates unique chunk IDs

Recommended settings:
- chunk_size: 800 characters
- chunk_overlap: 120 characters
"""

from typing import List, Dict, Any
import hashlib
from langchain_text_splitters import RecursiveCharacterTextSplitter


def generate_chunk_id(rag_type: str, source: str, chunk_index: int) -> str:
    """
    Generate a unique, deterministic chunk ID.
    
    Format: {rag_type}_{source}_{chunk_index}_{hash}
    
    Args:
        rag_type: 'brand', 'policy', or 'safety'
        source: Source filename
        chunk_index: Index of chunk within the document
        
    Returns:
        str: Unique chunk ID
    """
    prefix = f"{rag_type}_{source}_{chunk_index}"
    hash_obj = hashlib.md5(prefix.encode())
    hash_suffix = hash_obj.hexdigest()[:8]
    return f"{prefix}_{hash_suffix}"


def chunk_document(
    doc: Dict[str, Any],
    chunk_size: int = 800,
    chunk_overlap: int = 120
) -> List[Dict[str, Any]]:
    """
    Split a single document into chunks.
    
    Splits on Markdown headings (#, ##, ###) as separators, with fallback
    to recursive character splitting.
    
    Args:
        doc: Document dictionary with 'text', 'source', 'rag_type', etc.
        chunk_size: Target chunk size in characters
        chunk_overlap: Overlap between consecutive chunks
        
    Returns:
        List of chunk dictionaries with keys:
        - text: Chunk content
        - chunk_id: Unique chunk identifier
        - rag_type: From original document
        - category: From original document
        - source: From original document
        - relative_path: From original document
    """
    
    text = doc['text']
    
    if not text.strip():
        print(f"⚠️  Warning: Empty document text for {doc['source']}")
        return []
    
    # Use Markdown-aware splitting with headings as separators
    splitter = RecursiveCharacterTextSplitter(
        separators=[
            "\n#{1,6} ",  # Markdown headings (highest priority)
            "\n\n",       # Paragraph breaks
            "\n",         # Line breaks
            " ",          # Words
            ""            # Characters (fallback)
        ],
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    
    text_chunks = splitter.split_text(text)
    
    chunks = []
    for idx, chunk_text in enumerate(text_chunks):
        if not chunk_text.strip():
            continue
        
        chunk_id = generate_chunk_id(
            rag_type=doc['rag_type'],
            source=doc['source'],
            chunk_index=idx
        )
        
        chunk = {
            'text': chunk_text.strip(),
            'chunk_id': chunk_id,
            'rag_type': doc['rag_type'],
            'category': doc['category'],
            'source': doc['source'],
            'relative_path': doc['relative_path'],
        }
        
        chunks.append(chunk)
    
    return chunks


def chunk_documents(
    documents: List[Dict[str, Any]],
    chunk_size: int = 800,
    chunk_overlap: int = 120
) -> List[Dict[str, Any]]:
    """
    Chunk all documents.
    
    Args:
        documents: List of document dictionaries from loader
        chunk_size: Target chunk size in characters
        chunk_overlap: Overlap between consecutive chunks
        
    Returns:
        Flat list of all chunks with metadata
    """
    
    all_chunks = []
    
    for doc in documents:
        chunks = chunk_document(doc, chunk_size, chunk_overlap)
        all_chunks.extend(chunks)
    
    return all_chunks


def print_chunking_stats(documents: List[Dict[str, Any]], chunks: List[Dict[str, Any]]) -> None:
    """
    Print chunking statistics.
    
    Args:
        documents: Original document list
        chunks: Chunk list after splitting
    """
    stats_by_type = {'brand': 0, 'policy': 0, 'safety': 0}
    
    for chunk in chunks:
        rag_type = chunk['rag_type']
        stats_by_type[rag_type] += 1
    
    print("\n" + "="*50)
    print("DOCUMENT CHUNKING STATISTICS")
    print("="*50)
    print(f"Total documents: {len(documents)}")
    print(f"Total chunks:    {len(chunks)}")
    print("-"*50)
    print("Chunks by RAG type:")
    print(f"  BRAND:  {stats_by_type['brand']} chunks")
    print(f"  POLICY: {stats_by_type['policy']} chunks")
    print(f"  SAFETY: {stats_by_type['safety']} chunks")
    print("="*50 + "\n")


def main():
    """
    Demo: Load and chunk documents.
    """
    from loader import load_markdown_files
    from pathlib import Path
    
    project_root = Path(__file__).parent.parent
    
    print("Loading documents...")
    documents = load_markdown_files(project_root)
    
    if not documents:
        print("❌ No documents loaded.")
        return
    
    print("Chunking documents...")
    chunks = chunk_documents(documents, chunk_size=800, chunk_overlap=120)
    
    if chunks:
        print_chunking_stats(documents, chunks)
        print("First chunk example:")
        print(f"  Chunk ID: {chunks[0]['chunk_id']}")
        print(f"  RAG Type: {chunks[0]['rag_type']}")
        print(f"  Source: {chunks[0]['source']}")
        print(f"  Text length: {len(chunks[0]['text'])} characters")
        print(f"  Text preview: {chunks[0]['text'][:100]}...")
    else:
        print("❌ No chunks generated.")


if __name__ == '__main__':
    main()
