import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from database.operations import get_paper_by_filename, list_all_papers
from semantic_chunked_pdf_rag import PAPERS_DIR
import subprocess
import json

async def main():
    # Get all PDF files
    all_pdfs = sorted([f.name for f in PAPERS_DIR.glob("*.pdf")])
    print(f"Found {len(all_pdfs)} PDF files")
    
    # Get already indexed papers
    indexed_papers = list_all_papers()
    indexed_filenames = {p['filename'] for p in indexed_papers}
    print(f"Already indexed: {len(indexed_filenames)} papers")
    
    # Find papers that need indexing
    to_index = [pdf for pdf in all_pdfs if pdf not in indexed_filenames]
    print(f"Need to index: {len(to_index)} papers")
    
    # Print list of papers to index
    print("\nPapers to index:")
    for i, pdf in enumerate(to_index[:50], 1):  # Show first 50
        print(f"{i}. {pdf}")
    
    if len(to_index) > 50:
        print(f"... and {len(to_index) - 50} more")
    
    print(f"\nTotal to process: {len(to_index)} papers")
    print(f"Current embeddings: {len(indexed_papers)} papers indexed")

if __name__ == "__main__":
    asyncio.run(main())
