#!/usr/bin/env python3
"""
Test MCP tools for Phase 5 by actually calling them.
"""
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import the MCP server module
import semantic_chunked_pdf_rag as mcp_server

# Access the underlying functions from the MCP tools
index_pdf = mcp_server.mcp.tools["index_pdf"].fn
list_indexed_papers = mcp_server.mcp.tools["list_indexed_papers"].fn
get_document_structure = mcp_server.mcp.tools["get_document_structure"].fn
generate_embeddings = mcp_server.mcp.tools["generate_embeddings"].fn
search_research_papers = mcp_server.mcp.tools["search_research_papers"].fn
get_document_section = mcp_server.mcp.tools["get_document_section"].fn

def print_result(tool_name, result):
    """Pretty print tool result."""
    print(f"\n{'='*80}")
    print(f"Tool: {tool_name}")
    print('='*80)
    print(json.dumps(result, indent=2, default=str))
    return result.get('success', False)


def test_index_pdf():
    """Test indexing a PDF."""
    print("\n🔧 TEST 1: Index PDF")
    
    # Use a known test PDF
    filename = "2501.05485v1.pdf"
    
    result = index_pdf(
        filename=filename,
        url="https://example.com/test.pdf",
        method="header"
    )
    
    success = print_result("index_pdf", result)
    
    if success:
        print(f"\n✅ Successfully indexed {filename}")
        print(f"   Paper ID: {result.get('paper_id')}")
        print(f"   Chunks: {result.get('num_chunks')}")
        print(f"   Sections: {result.get('num_sections', 'N/A')}")
    else:
        print(f"\n❌ Failed to index {filename}: {result.get('message')}")
    
    return success


def test_list_indexed_papers():
    """Test listing indexed papers."""
    print("\n🔧 TEST 2: List Indexed Papers")
    
    result = list_indexed_papers()
    success = print_result("list_indexed_papers", result)
    
    if success:
        print(f"\n✅ Found {result.get('count', 0)} indexed papers")
        for i, paper in enumerate(result.get('papers', [])[:3], 1):
            print(f"   {i}. {paper['filename']} ({paper.get('num_chunks')} chunks)")
    
    return success


def test_get_document_structure():
    """Test getting document structure."""
    print("\n🔧 TEST 3: Get Document Structure")
    
    filename = "2501.05485v1.pdf"
    result = get_document_structure(filename=filename)
    success = print_result("get_document_structure", result)
    
    if success:
        structure = result.get('structure', {})
        print(f"\n✅ Retrieved structure for {filename}")
        print(f"   Title: {structure.get('title', 'N/A')}")
        print(f"   Chunks: {structure.get('num_chunks')}")
        print(f"   Sections: {len(structure.get('sections', []))}")
        
        # Show first 3 sections
        for i, section in enumerate(structure.get('sections', [])[:3], 1):
            print(f"   {i}. {section['header_path']} "
                  f"(chunks {section['start_chunk_index']}-{section['end_chunk_index']})")
    
    return success


def test_generate_embeddings():
    """Test generating embeddings."""
    print("\n🔧 TEST 4: Generate Embeddings")
    
    filename = "2501.05485v1.pdf"
    print(f"Generating embeddings for {filename}...")
    print("(This may take a minute...)")
    
    result = generate_embeddings(filename=filename)
    success = print_result("generate_embeddings", result)
    
    if success:
        print(f"\n✅ Generated embeddings for {filename}")
        print(f"   Embeddings: {result.get('num_embeddings')}")
        print(f"   Dimension: {result.get('embedding_dim')}")
        print(f"   Model: {result.get('model_name')}")
        print(f"   Total vectors in FAISS: {result.get('faiss_total_vectors')}")
    
    return success


def test_search_research_papers():
    """Test semantic search."""
    print("\n🔧 TEST 5: Search Research Papers")
    
    query = "What is semantic chunking and how does it work?"
    print(f"Query: '{query}'")
    
    result = search_research_papers(
        query=query,
        k=3,
        context_window=1
    )
    success = print_result("search_research_papers", result)
    
    if success:
        print(f"\n✅ Search completed")
        print(f"   Query: {result.get('query')}")
        print(f"   Results: {result.get('num_results')}")
        
        # Show top 3 results
        for i, res in enumerate(result.get('results', [])[:3], 1):
            is_context = res.get('is_context', False)
            marker = "[CONTEXT]" if is_context else "[MATCH]"
            dist = res.get('distance')
            dist_str = f"{dist:.4f}" if dist is not None else "N/A"
            
            print(f"\n   {marker} Result {i}:")
            print(f"   - File: {res.get('filename')}")
            print(f"   - Chunk: {res.get('chunk_index')}")
            print(f"   - Distance: {dist_str}")
            print(f"   - Header: {res.get('header_path', 'N/A')}")
            print(f"   - Text: {res.get('text', '')[:100]}...")
    
    return success


def test_get_document_section():
    """Test getting document sections."""
    print("\n🔧 TEST 6: Get Document Section")
    
    filename = "2501.05485v1.pdf"
    
    # Test 1: Get by chunk index
    print(f"\n--- Query by chunk_index ---")
    result1 = get_document_section(filename=filename, chunk_index=0)
    
    if result1.get('success'):
        print(f"✅ Retrieved chunk 0")
        chunk = result1.get('chunks', [{}])[0]
        print(f"   Text length: {len(chunk.get('text', ''))}")
        print(f"   Header: {chunk.get('header_path', 'N/A')}")
    
    # Test 2: Get by page range
    print(f"\n--- Query by page range ---")
    result2 = get_document_section(filename=filename, page_start=0, page_end=1)
    
    if result2.get('success'):
        print(f"✅ Retrieved chunks for pages 0-1")
        print(f"   Chunks: {result2.get('num_chunks')}")
        for chunk in result2.get('chunks', []):
            print(f"   - Chunk {chunk['chunk_index']}: "
                  f"pages {chunk['page_start']}-{chunk['page_end']}")
    
    # Test 3: Get by header path (if available)
    print(f"\n--- Query by header_path ---")
    # First get structure to find a header
    struct_result = get_document_structure(filename=filename)
    if struct_result.get('success'):
        sections = struct_result.get('structure', {}).get('sections', [])
        if sections:
            first_header = sections[0]['header_path']
            result3 = get_document_section(filename=filename, header_path=first_header)
            
            if result3.get('success'):
                print(f"✅ Retrieved section: {first_header}")
                print(f"   Chunks: {result3.get('num_chunks')}")
        else:
            print("⚠️  No sections available (might be using S2 chunking)")
    
    return True


def main():
    """Run all tests."""
    print("="*80)
    print("PHASE 5 MCP TOOLS TEST")
    print("Testing PDF indexing and query tools")
    print("="*80)
    
    results = []
    
    # Test 1: Index PDF
    try:
        results.append(("Index PDF", test_index_pdf()))
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Index PDF", False))
    
    # Test 2: List papers
    try:
        results.append(("List Papers", test_list_indexed_papers()))
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        results.append(("List Papers", False))
    
    # Test 3: Get structure
    try:
        results.append(("Get Structure", test_get_document_structure()))
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        results.append(("Get Structure", False))
    
    # Test 4: Generate embeddings
    try:
        results.append(("Generate Embeddings", test_generate_embeddings()))
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Generate Embeddings", False))
    
    # Test 5: Search (only if embeddings succeeded)
    if results[-1][1]:  # Check if embeddings succeeded
        try:
            results.append(("Search Papers", test_search_research_papers()))
        except Exception as e:
            print(f"\n❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append(("Search Papers", False))
    else:
        print("\n⚠️  Skipping search test (embeddings not available)")
        results.append(("Search Papers", False))
    
    # Test 6: Get sections
    try:
        results.append(("Get Sections", test_get_document_section()))
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        results.append(("Get Sections", False))
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    passed = sum(1 for _, s in results if s)
    total = len(results)
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

