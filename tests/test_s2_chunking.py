#!/usr/bin/env python3
"""
Test script comparing header-based and S2 chunking methods.
"""
import sys
from pathlib import Path
import fitz

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from pdf_processing import extract_text_with_headers, validate_pdf_content
from chunking import chunk_by_headers, chunk_by_s2

def compare_chunking_methods(filename: str):
    """Compare header-based vs S2 chunking on a PDF."""
    filepath = Path("./papers") / filename
    
    if not filepath.exists():
        print(f"Error: PDF file not found: {filepath}")
        return False
    
    # Validate and open PDF
    with open(filepath, 'rb') as f:
        content = f.read()
    
    if not validate_pdf_content(content):
        print(f"Error: File is not a valid PDF: {filepath}")
        return False
    
    doc = fitz.open(filepath)
    print(f"✓ Opened PDF: {len(doc)} pages")
    
    # Extract segments
    segments = extract_text_with_headers(doc)
    print(f"✓ Extracted {len(segments)} text segments\n")
    
    # Method 1: Header-based chunking
    print("="*80)
    print("METHOD 1: HEADER-BASED CHUNKING")
    print("="*80)
    header_chunks = chunk_by_headers(segments)
    print(f"Created {len(header_chunks)} chunks\n")
    
    for i, chunk in enumerate(header_chunks[:5]):
        print(f"Chunk {i}:")
        print(f"  Header path: {chunk['header_path'][:80] if chunk['header_path'] else '(none)'}")
        print(f"  Pages: {chunk['page_start']+1}-{chunk['page_end']+1}")
        print(f"  Length: {len(chunk['text'])} chars")
        preview = chunk['text'][:150].replace('\n', ' ')
        print(f"  Preview: {preview}...\n")
    
    # Method 2: S2 chunking
    print("="*80)
    print("METHOD 2: S2 CHUNKING (Spatial-Semantic)")
    print("="*80)
    s2_chunks = chunk_by_s2(segments, max_token_length=512)
    print(f"Created {len(s2_chunks)} chunks\n")
    
    for i, chunk in enumerate(s2_chunks[:5]):
        print(f"Chunk {i}:")
        print(f"  Pages: {chunk['page_start']+1}-{chunk['page_end']+1}")
        print(f"  Length: {len(chunk['text'])} chars")
        preview = chunk['text'][:150].replace('\n', ' ')
        print(f"  Preview: {preview}...\n")
    
    print("="*80)
    print("COMPARISON SUMMARY")
    print("="*80)
    print(f"Header-based chunks: {len(header_chunks)}")
    print(f"S2 chunks: {len(s2_chunks)}")
    print(f"\nHeader-based avg size: {sum(len(c['text']) for c in header_chunks) / len(header_chunks):.0f} chars")
    print(f"S2 avg size: {sum(len(c['text']) for c in s2_chunks) / len(s2_chunks):.0f} chars")
    
    doc.close()
    return True

if __name__ == "__main__":
    filename = "2501.05485v1.pdf"
    success = compare_chunking_methods(filename)
    sys.exit(0 if success else 1)

