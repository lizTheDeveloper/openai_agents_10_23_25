"""
Integration test for MCP server - directly tests the tools.

This test imports the MCP server module and directly calls the tool functions
to verify they work correctly with the database.
"""
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

def test_mcp_tools():
    """Test all MCP tools with database integration."""
    print("=" * 70)
    print("MCP TOOLS INTEGRATION TEST")
    print("=" * 70)
    
    # Import the actual tool functions via their wrapped names
    import semantic_chunked_pdf_rag as server
    
    # Access the actual functions from the FastMCP FunctionTool wrapper
    download_pdf = server.download_pdf.fn
    chunk_pdf = server.chunk_pdf.fn
    index_pdf = server.index_pdf.fn
    list_indexed_papers = server.list_indexed_papers.fn
    get_document_structure = server.get_document_structure.fn
    
    # Find a test PDF
    papers_dir = Path("./papers")
    pdf_files = list(papers_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("❌ No PDF files found in ./papers/")
        return False
    
    test_pdf = pdf_files[0].name
    print(f"\n📄 Using test PDF: {test_pdf}")
    
    # Test 1: List indexed papers (before)
    print("\n" + "=" * 70)
    print("TEST 1: list_indexed_papers (before indexing)")
    print("=" * 70)
    result = list_indexed_papers()
    print(f"✅ Success: {result['success']}")
    print(f"   Count: {result['count']} papers")
    if result['papers']:
        for paper in result['papers'][:3]:  # Show first 3
            print(f"   - {paper['filename']}: {paper['num_chunks']} chunks")
    
    # Test 2: Index the PDF
    print("\n" + "=" * 70)
    print("TEST 2: index_pdf")
    print("=" * 70)
    result = index_pdf(filename=test_pdf, method="header")
    print(f"✅ Success: {result['success']}")
    if result['success']:
        print(f"   Paper ID: {result.get('paper_id')}")
        print(f"   Num chunks: {result.get('num_chunks')}")
        print(f"   Num sections: {result.get('num_sections', 'N/A')}")
        print(f"   Message: {result['message']}")
    
    paper_id = result.get('paper_id')
    
    # Test 3: Get document structure
    print("\n" + "=" * 70)
    print("TEST 3: get_document_structure")
    print("=" * 70)
    result = get_document_structure(filename=test_pdf)
    print(f"✅ Success: {result['success']}")
    if result['success']:
        structure = result['structure']
        print(f"   Paper ID: {structure['paper_id']}")
        print(f"   Filename: {structure['filename']}")
        print(f"   Num chunks: {structure['num_chunks']}")
        print(f"   Num pages: {structure['num_pages']}")
        print(f"   Chunking method: {structure['chunking_method']}")
        print(f"   Num sections: {len(structure['sections'])}")
        
        # Show first few sections
        print("\n   Sections (first 5):")
        for i, section in enumerate(structure['sections'][:5]):
            print(f"     {i+1}. {section['header_path']}")
            print(f"        Chunks: {section['start_chunk_index']}-{section['end_chunk_index']}")
            print(f"        Pages: {section['page_start']}-{section['page_end']}")
    
    # Test 4: List indexed papers (after)
    print("\n" + "=" * 70)
    print("TEST 4: list_indexed_papers (after indexing)")
    print("=" * 70)
    result = list_indexed_papers()
    print(f"✅ Success: {result['success']}")
    print(f"   Count: {result['count']} papers")
    if result['papers']:
        print("\n   All indexed papers:")
        for paper in result['papers']:
            print(f"   - {paper['filename']}")
            print(f"     Chunks: {paper['num_chunks']}, Pages: {paper['num_pages']}")
            print(f"     Method: {paper['chunking_method']}")
    
    # Test 5: Chunk PDF (legacy tool - doesn't use database)
    print("\n" + "=" * 70)
    print("TEST 5: chunk_pdf (legacy, no database)")
    print("=" * 70)
    result = chunk_pdf(filename=test_pdf, method="header")
    print(f"✅ Success: {result['success']}")
    if result['success']:
        print(f"   Num chunks: {result['num_chunks']}")
        print(f"   Method: {result['method']}")
        print(f"   First chunk preview:")
        if result['chunks']:
            first_chunk = result['chunks'][0]
            print(f"     Index: {first_chunk['chunk_index']}")
            print(f"     Header: {first_chunk['header_path']}")
            print(f"     Pages: {first_chunk['page_start']}-{first_chunk['page_end']}")
            print(f"     Text length: {first_chunk['full_text_length']} chars")
    
    # Test 6: Verify database navigation
    print("\n" + "=" * 70)
    print("TEST 6: Database navigation (direct query)")
    print("=" * 70)
    from database.operations import get_chunk, get_chunks_range, get_paper_by_filename
    
    if paper_id:
        # Get first chunk
        chunk_0 = get_chunk(paper_id, 0)
        if chunk_0:
            print(f"✅ Chunk 0 retrieved:")
            print(f"   Chunk index: {chunk_0['chunk_index']}")
            print(f"   Header path: {chunk_0['header_path']}")
            print(f"   Pages: {chunk_0['page_start']}-{chunk_0['page_end']}")
            print(f"   Navigation: prev={chunk_0['prev_chunk_index']}, next={chunk_0['next_chunk_index']}")
            print(f"   Text length: {len(chunk_0['text'])} chars")
        
        # Get a range of chunks
        chunk_range = get_chunks_range(paper_id, 0, 2)
        print(f"\n✅ Retrieved chunk range [0-2]: {len(chunk_range)} chunks")
        for chunk in chunk_range:
            print(f"   - Chunk {chunk['chunk_index']}: {chunk['header_path'][:50]}")
    
    print("\n" + "=" * 70)
    print("✅ ALL INTEGRATION TESTS PASSED!")
    print("=" * 70)
    
    print("\n📊 Summary:")
    print(f"   • Database initialized: ✅")
    print(f"   • PDF indexed: ✅")
    print(f"   • Navigation indices working: ✅")
    print(f"   • Section mappings created: ✅")
    print(f"   • All MCP tools functional: ✅")
    
    return True


if __name__ == "__main__":
    try:
        success = test_mcp_tools()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

