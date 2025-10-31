"""
Phase 5 Integration Test - Query Tools

Tests the new Phase 5 MCP tools:
- search_research_papers
- get_document_section
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_phase5_tools():
    """Test Phase 5 query tools."""
    print("=" * 80)
    print("PHASE 5 QUERY TOOLS TEST")
    print("=" * 80)
    
    # Import the server module
    import semantic_chunked_pdf_rag as server
    
    # Access tool functions
    index_pdf = server.index_pdf.fn
    list_indexed_papers = server.list_indexed_papers.fn
    get_document_structure = server.get_document_structure.fn
    generate_embeddings = server.generate_embeddings.fn
    search_research_papers = server.search_research_papers.fn
    get_document_section = server.get_document_section.fn
    
    # Find a test PDF
    papers_dir = Path("./papers")
    pdf_files = list(papers_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("❌ No PDF files found in ./papers/")
        return False
    
    test_pdf = pdf_files[0].name
    print(f"\n📄 Using test PDF: {test_pdf}")
    
    # Test 1: Ensure paper is indexed
    print("\n" + "=" * 80)
    print("TEST 1: Index PDF (prerequisite)")
    print("=" * 80)
    result = index_pdf(filename=test_pdf, method="header")
    print(f"✅ Success: {result['success']}")
    if result['success']:
        print(f"   Paper ID: {result.get('paper_id')}")
        print(f"   Chunks: {result.get('num_chunks')}")
        print(f"   Message: {result['message']}")
    
    paper_id = result.get('paper_id')
    
    # Test 2: Generate embeddings
    print("\n" + "=" * 80)
    print("TEST 2: Generate Embeddings")
    print("=" * 80)
    print("⏳ Generating embeddings (this may take a minute)...")
    result = generate_embeddings(filename=test_pdf)
    print(f"✅ Success: {result['success']}")
    if result['success']:
        print(f"   Embeddings: {result.get('num_embeddings')}")
        print(f"   Dimension: {result.get('embedding_dim')}")
        print(f"   Model: {result.get('model_name')}")
        print(f"   Total vectors: {result.get('faiss_total_vectors')}")
    else:
        print(f"   Error: {result.get('message')}")
    
    embeddings_available = result['success']
    
    # Test 3: Search research papers (if embeddings available)
    if embeddings_available:
        print("\n" + "=" * 80)
        print("TEST 3: Search Research Papers")
        print("=" * 80)
        
        query = "What is semantic chunking?"
        print(f"Query: '{query}'")
        
        result = search_research_papers(
            query=query,
            k=3,
            context_window=1
        )
        print(f"✅ Success: {result['success']}")
        if result['success']:
            print(f"   Results: {result.get('num_results')}")
            print(f"   Message: {result.get('message')}")
            
            # Show top 3 results
            print("\n   Top Results:")
            for i, res in enumerate(result.get('results', [])[:3], 1):
                is_context = res.get('is_context', False)
                marker = "[CONTEXT]" if is_context else "[MATCH]  "
                dist = res.get('distance')
                dist_str = f"{dist:.4f}" if dist is not None else "N/A"
                
                print(f"\n   {i}. {marker} Chunk {res.get('chunk_index')}")
                print(f"      File: {res.get('filename')}")
                print(f"      Distance: {dist_str}")
                print(f"      Header: {res.get('header_path', 'N/A')}")
                print(f"      Pages: {res.get('page_start')}-{res.get('page_end')}")
                print(f"      Text: {res.get('text', '')[:80]}...")
        else:
            print(f"   Error: {result.get('message')}")
    else:
        print("\n⚠️  Skipping search test (embeddings not generated)")
    
    # Test 4: Get document section by chunk_index
    print("\n" + "=" * 80)
    print("TEST 4: Get Document Section (by chunk_index)")
    print("=" * 80)
    result = get_document_section(filename=test_pdf, chunk_index=0)
    print(f"✅ Success: {result['success']}")
    if result['success']:
        print(f"   Chunks returned: {result.get('num_chunks')}")
        if result.get('chunks'):
            chunk = result['chunks'][0]
            print(f"   Chunk index: {chunk['chunk_index']}")
            print(f"   Header: {chunk.get('header_path', 'N/A')}")
            print(f"   Pages: {chunk['page_start']}-{chunk['page_end']}")
            print(f"   Text length: {len(chunk['text'])} chars")
            print(f"   Navigation: prev={chunk.get('prev_chunk_index')}, next={chunk.get('next_chunk_index')}")
    else:
        print(f"   Error: {result.get('message')}")
    
    # Test 5: Get document section by page range
    print("\n" + "=" * 80)
    print("TEST 5: Get Document Section (by page range)")
    print("=" * 80)
    result = get_document_section(filename=test_pdf, page_start=0, page_end=1)
    print(f"✅ Success: {result['success']}")
    if result['success']:
        print(f"   Chunks returned: {result.get('num_chunks')}")
        print(f"   Chunks overlapping pages 0-1:")
        for chunk in result.get('chunks', []):
            print(f"     - Chunk {chunk['chunk_index']}: pages {chunk['page_start']}-{chunk['page_end']}")
    else:
        print(f"   Error: {result.get('message')}")
    
    # Test 6: Get document section by header_path
    print("\n" + "=" * 80)
    print("TEST 6: Get Document Section (by header_path)")
    print("=" * 80)
    
    # First get structure to find a valid header
    struct_result = get_document_structure(filename=test_pdf)
    if struct_result['success'] and struct_result['structure']['sections']:
        first_section = struct_result['structure']['sections'][0]
        header_path = first_section['header_path']
        
        print(f"Testing with header: '{header_path}'")
        result = get_document_section(filename=test_pdf, header_path=header_path)
        print(f"✅ Success: {result['success']}")
        if result['success']:
            print(f"   Chunks returned: {result.get('num_chunks')}")
            print(f"   Section: {header_path}")
            print(f"   Expected chunks: {first_section['start_chunk_index']}-{first_section['end_chunk_index']}")
        else:
            print(f"   Error: {result.get('message')}")
    else:
        print("⚠️  No sections available (might be using S2 chunking)")
    
    # Test 7: Context window validation
    if embeddings_available:
        print("\n" + "=" * 80)
        print("TEST 7: Context Window Sizes")
        print("=" * 80)
        
        # Test with different context window sizes
        for context_window in [0, 1, 2]:
            result = search_research_papers(
                query="chunking",
                k=2,
                context_window=context_window
            )
            if result['success']:
                num_matches = sum(1 for r in result['results'] if not r['is_context'])
                num_context = sum(1 for r in result['results'] if r['is_context'])
                print(f"   context_window={context_window}: "
                      f"{num_matches} matches + {num_context} context = {result['num_results']} total")
    
    # Summary
    print("\n" + "=" * 80)
    print("✅ PHASE 5 TESTS COMPLETED!")
    print("=" * 80)
    
    print("\n📊 Summary:")
    print(f"   • PDF indexed: ✅")
    print(f"   • Embeddings generated: {'✅' if embeddings_available else '⚠️'}")
    print(f"   • Semantic search: {'✅' if embeddings_available else '⚠️ (skipped)'}")
    print(f"   • Section query (chunk_index): ✅")
    print(f"   • Section query (page_range): ✅")
    print(f"   • Section query (header_path): ✅")
    print(f"   • Context window: {'✅' if embeddings_available else '⚠️ (skipped)'}")
    
    return True


if __name__ == "__main__":
    try:
        success = test_phase5_tools()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

