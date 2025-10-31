"""
Integration tests for Phase 5: Query Tools Implementation

This test suite validates the search and retrieval functionality including:
- Semantic search with FAISS
- Context window retrieval
- Document section queries by chunk_index, header_path, and page range
"""
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from database.operations import (
    initialize_database,
    get_paper_by_filename,
    get_chunks_range,
    get_chunks_by_page_range,
    get_section,
    get_chunk,
    get_chunks_by_ids
)
from embeddings import get_embedding_generator, FAISSIndexManager
from utils.logger import get_logger

logger = get_logger()


def test_database_query_functions():
    """Test the new database query functions added in Phase 5."""
    print("\n" + "="*80)
    print("TEST 1: Database Query Functions")
    print("="*80)
    
    # Initialize database
    if not initialize_database():
        print("❌ Failed to initialize database")
        return False
    
    # Get a test paper (assuming we have papers indexed from previous phases)
    test_filename = "2501.05485v1.pdf"
    paper = get_paper_by_filename(test_filename)
    
    if not paper:
        print(f"⚠️  Test paper not found: {test_filename}")
        print("   Please run Phase 3 tests first to index papers")
        return False
    
    paper_id = paper["paper_id"]
    print(f"✅ Found test paper: {test_filename} (paper_id={paper_id})")
    print(f"   Title: {paper.get('title', 'N/A')}")
    print(f"   Chunks: {paper.get('num_chunks', 0)}")
    
    # Test 1: get_chunk
    print("\n--- Testing get_chunk ---")
    chunk = get_chunk(paper_id, 0)
    if chunk:
        print(f"✅ Retrieved chunk 0: {len(chunk['text'])} chars")
        print(f"   Header: {chunk.get('header_path', 'N/A')}")
        print(f"   Pages: {chunk['page_start']}-{chunk['page_end']}")
    else:
        print("❌ Failed to retrieve chunk 0")
        return False
    
    # Test 2: get_chunks_range
    print("\n--- Testing get_chunks_range ---")
    chunks = get_chunks_range(paper_id, 0, 2)
    if chunks:
        print(f"✅ Retrieved {len(chunks)} chunks (indices 0-2)")
        for c in chunks:
            print(f"   Chunk {c['chunk_index']}: {len(c['text'])} chars, pages {c['page_start']}-{c['page_end']}")
    else:
        print("❌ Failed to retrieve chunk range")
        return False
    
    # Test 3: get_chunks_by_page_range
    print("\n--- Testing get_chunks_by_page_range ---")
    page_chunks = get_chunks_by_page_range(paper_id, 0, 1)
    if page_chunks:
        print(f"✅ Retrieved {len(page_chunks)} chunks overlapping pages 0-1")
        for c in page_chunks:
            print(f"   Chunk {c['chunk_index']}: pages {c['page_start']}-{c['page_end']}")
    else:
        print("⚠️  No chunks found for page range 0-1")
    
    # Test 4: get_section (if header-based chunking was used)
    print("\n--- Testing get_section ---")
    if paper.get('chunking_method') == 'header':
        # Try to get the first chunk's section
        first_chunk = get_chunk(paper_id, 0)
        if first_chunk and first_chunk.get('header_path'):
            header_path = first_chunk['header_path']
            section = get_section(paper_id, header_path)
            if section:
                print(f"✅ Retrieved section: {header_path}")
                print(f"   Chunks: {section['start_chunk_index']}-{section['end_chunk_index']}")
                print(f"   Pages: {section['page_start']}-{section['page_end']}")
            else:
                print(f"⚠️  Section not found: {header_path}")
        else:
            print("⚠️  No header_path available in first chunk")
    else:
        print(f"⚠️  Paper uses '{paper.get('chunking_method')}' method, skipping section test")
    
    # Test 5: get_chunks_by_ids
    print("\n--- Testing get_chunks_by_ids ---")
    if chunks:
        chunk_ids = [c['chunk_id'] for c in chunks[:2]]
        retrieved_chunks = get_chunks_by_ids(chunk_ids)
        if retrieved_chunks:
            print(f"✅ Retrieved {len(retrieved_chunks)} chunks by IDs")
            for c in retrieved_chunks:
                print(f"   Chunk {c['chunk_index']}: {c.get('filename', 'N/A')}")
        else:
            print("❌ Failed to retrieve chunks by IDs")
            return False
    
    print("\n✅ All database query function tests passed!")
    return True


def test_faiss_search():
    """Test FAISS similarity search functionality."""
    print("\n" + "="*80)
    print("TEST 2: FAISS Similarity Search")
    print("="*80)
    
    # Check if FAISS index exists
    from embeddings.faiss_index import INDEXES_DIR
    index_path = INDEXES_DIR / "research_papers.faiss"
    
    if not index_path.exists():
        print(f"⚠️  FAISS index not found at {index_path}")
        print("   Please run generate_embeddings first")
        return False
    
    print(f"✅ FAISS index found: {index_path}")
    
    # Initialize embedding generator
    print("\n--- Initializing Embedding Generator ---")
    try:
        embedding_gen = get_embedding_generator()
        embedding_dim = embedding_gen.get_embedding_dimension()
        print(f"✅ Embedding generator initialized (dim={embedding_dim})")
    except Exception as e:
        print(f"❌ Failed to initialize embedding generator: {e}")
        return False
    
    # Initialize FAISS index manager
    print("\n--- Loading FAISS Index ---")
    faiss_manager = FAISSIndexManager(
        index_name="research_papers",
        embedding_dim=embedding_dim
    )
    
    if not faiss_manager.load_index():
        print("❌ Failed to load FAISS index")
        return False
    
    print(f"✅ FAISS index loaded: {faiss_manager.index.ntotal} vectors")
    print(f"   Mappings: {len(faiss_manager.embedding_to_chunk)}")
    
    # Test search
    print("\n--- Testing Semantic Search ---")
    test_query = "What is semantic chunking?"
    
    try:
        query_embeddings = embedding_gen.generate_embeddings([test_query], batch_size=1)
        query_embedding = query_embeddings[0]
        print(f"✅ Generated query embedding: shape {query_embedding.shape}")
    except Exception as e:
        print(f"❌ Failed to generate query embedding: {e}")
        return False
    
    try:
        chunk_ids, distances = faiss_manager.search(query_embedding, k=5)
        print(f"✅ Search completed: found {len(chunk_ids)} results")
        
        for i, (chunk_id, dist) in enumerate(zip(chunk_ids, distances)):
            print(f"   {i+1}. Chunk ID {chunk_id}, distance: {dist:.4f}")
        
        # Retrieve chunks with metadata
        if chunk_ids:
            chunks = get_chunks_by_ids(chunk_ids)
            print(f"\n✅ Retrieved {len(chunks)} chunks with metadata")
            for i, chunk in enumerate(chunks[:3]):  # Show first 3
                print(f"\n   Result {i+1}:")
                print(f"   - File: {chunk.get('filename', 'N/A')}")
                print(f"   - Chunk: {chunk['chunk_index']}")
                print(f"   - Header: {chunk.get('header_path', 'N/A')}")
                print(f"   - Text preview: {chunk['text'][:100]}...")
        
    except Exception as e:
        print(f"❌ Search failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n✅ FAISS search test passed!")
    return True


def test_context_window_retrieval():
    """Test context window retrieval functionality."""
    print("\n" + "="*80)
    print("TEST 3: Context Window Retrieval")
    print("="*80)
    
    test_filename = "2501.05485v1.pdf"
    paper = get_paper_by_filename(test_filename)
    
    if not paper:
        print(f"⚠️  Test paper not found: {test_filename}")
        return False
    
    paper_id = paper["paper_id"]
    num_chunks = paper.get("num_chunks", 0)
    
    print(f"✅ Using paper: {test_filename} ({num_chunks} chunks)")
    
    # Test context window for middle chunk
    if num_chunks < 5:
        print(f"⚠️  Paper has only {num_chunks} chunks, need at least 5 for this test")
        return False
    
    middle_chunk_idx = num_chunks // 2
    context_window = 2
    
    print(f"\n--- Testing context window around chunk {middle_chunk_idx} ---")
    start_idx = max(0, middle_chunk_idx - context_window)
    end_idx = min(num_chunks - 1, middle_chunk_idx + context_window)
    
    chunks = get_chunks_range(paper_id, start_idx, end_idx)
    
    if chunks:
        print(f"✅ Retrieved {len(chunks)} chunks (indices {start_idx}-{end_idx})")
        for c in chunks:
            is_center = c['chunk_index'] == middle_chunk_idx
            marker = ">>> " if is_center else "    "
            print(f"{marker}Chunk {c['chunk_index']}: {len(c['text'])} chars")
    else:
        print("❌ Failed to retrieve context chunks")
        return False
    
    print("\n✅ Context window retrieval test passed!")
    return True


def test_section_queries():
    """Test document section queries by different methods."""
    print("\n" + "="*80)
    print("TEST 4: Document Section Queries")
    print("="*80)
    
    test_filename = "2501.05485v1.pdf"
    paper = get_paper_by_filename(test_filename)
    
    if not paper:
        print(f"⚠️  Test paper not found: {test_filename}")
        return False
    
    paper_id = paper["paper_id"]
    print(f"✅ Using paper: {test_filename}")
    print(f"   Chunking method: {paper.get('chunking_method', 'N/A')}")
    
    # Test 1: Query by chunk_index
    print("\n--- Test: Query by chunk_index ---")
    chunk = get_chunk(paper_id, 0)
    if chunk:
        print(f"✅ Retrieved chunk by index 0")
        print(f"   Text length: {len(chunk['text'])} chars")
        print(f"   Header: {chunk.get('header_path', 'N/A')}")
    else:
        print("❌ Failed to retrieve chunk by index")
        return False
    
    # Test 2: Query by header_path (if using header-based chunking)
    if paper.get('chunking_method') == 'header':
        print("\n--- Test: Query by header_path ---")
        first_chunk = get_chunk(paper_id, 0)
        if first_chunk and first_chunk.get('header_path'):
            header_path = first_chunk['header_path']
            section = get_section(paper_id, header_path)
            if section:
                section_chunks = get_chunks_range(
                    paper_id,
                    section['start_chunk_index'],
                    section['end_chunk_index']
                )
                print(f"✅ Retrieved section: {header_path}")
                print(f"   Contains {len(section_chunks)} chunks")
            else:
                print(f"⚠️  Section not found: {header_path}")
        else:
            print("⚠️  No header_path in first chunk")
    else:
        print("\n⚠️  Paper not using header method, skipping header_path test")
    
    # Test 3: Query by page range
    print("\n--- Test: Query by page range ---")
    page_chunks = get_chunks_by_page_range(paper_id, 0, 2)
    if page_chunks:
        print(f"✅ Retrieved {len(page_chunks)} chunks for pages 0-2")
        for c in page_chunks:
            print(f"   Chunk {c['chunk_index']}: pages {c['page_start']}-{c['page_end']}")
    else:
        print("⚠️  No chunks found for pages 0-2")
    
    print("\n✅ Document section query tests completed!")
    return True


def run_all_tests():
    """Run all Phase 5 integration tests."""
    print("\n" + "="*80)
    print("PHASE 5 INTEGRATION TESTS")
    print("Query Tools Implementation")
    print("="*80)
    
    results = []
    
    # Run each test
    results.append(("Database Query Functions", test_database_query_functions()))
    results.append(("FAISS Similarity Search", test_faiss_search()))
    results.append(("Context Window Retrieval", test_context_window_retrieval()))
    results.append(("Document Section Queries", test_section_queries()))
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n🎉 All Phase 5 tests passed!")
    else:
        print("\n⚠️  Some tests failed. Please review the output above.")
    
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

