"""
Document Loader for Markdown Knowledge Bases

Loads Markdown (.md) files from:
- brand/knowledge/
- policy/knowledge/
- safety/knowledge/

Excludes evaluation/ and governance/ folders.
Returns list of document objects with metadata.
"""

from pathlib import Path
from typing import List, Dict, Any


def get_rag_type_from_path(file_path: Path) -> str:
    """
    Determine RAG type (brand, policy, safety) from file path.
    
    Args:
        file_path: Path object for the markdown file
        
    Returns:
        str: One of 'brand', 'policy', or 'safety'
    """
    parts = file_path.parts
    if 'brand' in parts:
        return 'brand'
    elif 'policy' in parts:
        return 'policy'
    elif 'safety' in parts:
        return 'safety'
    else:
        raise ValueError(f"Cannot determine RAG type from path: {file_path}")


def extract_category_from_filename(filename: str) -> str:
    """
    Extract category from filename by removing leading numbers and .md extension.
    
    Example:
        "02_Nexora_Plans_and_Subscriptions.md" -> "plans_and_subscriptions"
        
    Args:
        filename: Name of the markdown file
        
    Returns:
        str: Lowercase category name
    """
    # Remove numbers and underscore prefix (e.g., "02_")
    name = filename.replace('.md', '')
    
    # Skip leading numbers and underscore
    parts = name.split('_', 1)
    if len(parts) > 1:
        category = parts[1]
    else:
        category = parts[0]
    
    # Convert to lowercase and replace underscores with spaces for readability
    return category.lower().replace('_', ' ')


def load_markdown_files(project_root: Path) -> List[Dict[str, Any]]:
    """
    Load all Markdown files from knowledge bases.
    
    Scans:
    - {project_root}/brand/knowledge/
    - {project_root}/policy/knowledge/
    - {project_root}/safety/knowledge/
    
    Excludes:
    - evaluation/
    - governance/
    
    Args:
        project_root: Path to the RAG project root directory
        
    Returns:
        List of document dictionaries with keys:
        - text: Full document content
        - source: Filename
        - file_name: Filename
        - rag_type: 'brand', 'policy', or 'safety'
        - category: Document category derived from filename
        - relative_path: Relative path from project root
    """
    
    documents = []
    knowledge_bases = ['brand', 'policy', 'safety']
    
    for rag_type in knowledge_bases:
        knowledge_dir = project_root / rag_type / 'knowledge'
        
        if not knowledge_dir.exists():
            print(f"⚠️  Warning: {knowledge_dir} does not exist. Skipping {rag_type.upper()}.")
            continue
        
        # Recursively find all .md files
        md_files = sorted(knowledge_dir.glob('**/*.md'))
        
        for md_file in md_files:
            try:
                # Read file content
                with open(md_file, 'r', encoding='utf-8') as f:
                    text = f.read()
                
                if not text.strip():
                    print(f"⚠️  Warning: Empty file skipped: {md_file.name}")
                    continue
                
                # Extract metadata
                category = extract_category_from_filename(md_file.name)
                relative_path = str(md_file.relative_to(project_root))
                
                doc = {
                    'text': text,
                    'source': md_file.name,
                    'file_name': md_file.name,
                    'rag_type': rag_type,
                    'category': category,
                    'relative_path': relative_path,
                }
                
                documents.append(doc)
                
            except Exception as e:
                print(f"❌ Error loading {md_file}: {e}")
                continue
    
    return documents


def print_loading_stats(documents: List[Dict[str, Any]]) -> None:
    """
    Print document loading statistics.
    
    Args:
        documents: List of loaded document dictionaries
    """
    stats = {'brand': 0, 'policy': 0, 'safety': 0}
    
    for doc in documents:
        rag_type = doc['rag_type']
        stats[rag_type] += 1
    
    print("\n" + "="*50)
    print("DOCUMENT LOADING STATISTICS")
    print("="*50)
    print(f"BRAND:  {stats['brand']} documents loaded")
    print(f"POLICY: {stats['policy']} documents loaded")
    print(f"SAFETY: {stats['safety']} documents loaded")
    print("-"*50)
    print(f"TOTAL:  {sum(stats.values())} documents loaded")
    print("="*50 + "\n")


def main():
    """
    Demo: Load all documents from project root.
    """
    # Assume this script is in src/, so project root is parent directory
    project_root = Path(__file__).parent.parent
    
    print("Loading Markdown documents...")
    documents = load_markdown_files(project_root)
    
    if documents:
        print_loading_stats(documents)
        print("\nFirst document example:")
        print(f"  Source: {documents[0]['source']}")
        print(f"  RAG Type: {documents[0]['rag_type']}")
        print(f"  Category: {documents[0]['category']}")
        print(f"  Text length: {len(documents[0]['text'])} characters")
    else:
        print("❌ No documents loaded.")


if __name__ == '__main__':
    main()
