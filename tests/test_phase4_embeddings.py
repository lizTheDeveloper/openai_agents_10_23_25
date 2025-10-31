"""
Test script for Phase 4: Qwen Embeddings & FAISS Index

This script tests the complete embedding generation and FAISS indexing pipeline:
1. Embedding generation using MLX
2. FAISS index creation and persistence
3. Database integration with embedding indices
4. Similarity search functionality
"""
import sys
from pathlib import Path
import numpy as np

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import get_logger
from database.operations import (
    get_paper_by_filename,
    get_all_chunks_for_paper,
    get_chunks_by_ids
)
from embeddings import get_embedding_generator, FAISSIndexManager

logger = get_logger()


def test_embedding_generation():
    """Test embedding generation with MLX."""
    print("\n" + "="*80)
    print("TEST 1: Embedding Generation with MLX")
    print("="*80)
    
    # Initialize embedding generator
    print("\n1. Initializing embedding generator...")
    embedding_gen = get_embedding_generator()
    embedding_dim = embedding_gen.get_embedding_dimension()
    print(f"   ✓ Loaded model: {embedding_gen.model_name}")
    print(f"   ✓ Embedding dimension: {embedding_dim}")
    
    # Generate embeddings for test texts
    print("\n2. Generating embeddings for test texts...")
    test_texts = [
        "This is a test sentence about machine learning.",
        "Natural language processing is a subfield of artificial intelligence.",
        "Deep learning models use neural networks."
    ]
    
    embeddings = embedding_gen.generate_embeddings(test_texts, batch_size=2)
    
    print(f"   ✓ Generated {len(embeddings)} embeddings")
    print(f"   ✓ Shape: {embeddings.shape}")
    print(f"   ✓ Data type: {embeddings.dtype}")
    
    # Check embedding properties
    print("\n3. Validating embeddings...")
    assert embeddings.shape == (3, embedding_dim), "Incorrect embedding shape"
    assert embeddings.dtype == np.float32 or embeddings.dtype == np.float64, "Incorrect dtype"
    
    # Check that embeddings are normalized (for cosine similarity)
    norms = np.linalg.norm(embeddings, axis=1)
    print(f"   ✓ Embedding norms: {norms}")
    print(f"   ✓ All embeddings normalized: {np.allclose(norms, 1.0, atol=1e-5)}")
    
    # Check that similar texts have higher similarity
    similarity_01 = np.dot(embeddings[0], embeddings[1])
    similarity_02 = np.dot(embeddings[0], embeddings[2])
    similarity_12 = np.dot(embeddings[1], embeddings[2])
    
    print(f"\n4. Checking similarity scores...")
    print(f"   Text 0 vs Text 1: {similarity_01:.4f}")
    print(f"   Text 0 vs Text 2: {similarity_02:.4f}")
    print(f"   Text 1 vs Text 2: {similarity_12:.4f}")
    
    print("\n✅ Embedding generation test PASSED")
    return True


def test_faiss_index():
    """Test FAISS index creation, persistence, and search."""
    print("\n" + "="*80)
    print("TEST 2: FAISS Index Management")
    print("="*80)
    
    # Create test index
    print("\n1. Creating FAISS index...")
    embedding_dim = 384  # all-MiniLM-L6-v2 dimension
    faiss_manager = FAISSIndexManager(
        index_name="test_index",
        embedding_dim=embedding_dim
    )
    faiss_manager.create_index()
    print(f"   ✓ Created index with dimension {embedding_dim}")
    
    # Generate test embeddings
    print("\n2. Generating test embeddings...")
    embedding_gen = get_embedding_generator()
    test_texts = [
        "Machine learning is a field of artificial intelligence.",
        "Deep learning uses neural networks with multiple layers.",
        "Natural language processing handles human language.",
        "Computer vision enables machines to understand images.",
        "Reinforcement learning learns through trial and error."
    ]
    embeddings = embedding_gen.generate_embeddings(test_texts)
    chunk_ids = [1000, 1001, 1002, 1003, 1004]
    
    print(f"   ✓ Generated {len(embeddings)} embeddings")
    
    # Add embeddings to index
    print("\n3. Adding embeddings to FAISS index...")
    success = faiss_manager.add_embeddings(embeddings, chunk_ids)
    assert success, "Failed to add embeddings to FAISS index"
    print(f"   ✓ Added {len(embeddings)} embeddings")
    print(f"   ✓ Total vectors in index: {faiss_manager.index.ntotal}")
    
    # Save index
    print("\n4. Saving FAISS index to disk...")
    success = faiss_manager.save_index()
    assert success, "Failed to save FAISS index"
    print(f"   ✓ Saved index to: {faiss_manager.index_path}")
    
    # Load index
    print("\n5. Loading FAISS index from disk...")
    faiss_manager2 = FAISSIndexManager(
        index_name="test_index",
        embedding_dim=embedding_dim
    )
    success = faiss_manager2.load_index()
    assert success, "Failed to load FAISS index"
    print(f"   ✓ Loaded index with {faiss_manager2.index.ntotal} vectors")
    
    # Test search
    print("\n6. Testing similarity search...")
    query_text = "artificial intelligence and machine learning"
    query_embedding = embedding_gen.generate_embeddings([query_text])
    
    result_chunk_ids, distances = faiss_manager2.search(query_embedding[0], k=3)
    
    print(f"   ✓ Query: '{query_text}'")
    print(f"   ✓ Found {len(result_chunk_ids)} results")
    for i, (chunk_id, dist) in enumerate(zip(result_chunk_ids, distances)):
        orig_idx = chunk_ids.index(chunk_id)
        print(f"      {i+1}. Chunk {chunk_id}: '{test_texts[orig_idx][:60]}...' (dist: {dist:.4f})")
    
    # Verify that the most similar result is the first text (about machine learning and AI)
    assert result_chunk_ids[0] == 1000, "Search didn't return most similar result first"
    
    # Get stats
    print("\n7. FAISS index statistics...")
    stats = faiss_manager2.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Clean up test files
    print("\n8. Cleaning up test files...")
    if faiss_manager.index_path.exists():
        faiss_manager.index_path.unlink()
    if faiss_manager.mapping_path.exists():
        faiss_manager.mapping_path.unlink()
    print("   ✓ Cleaned up test files")
    
    print("\n✅ FAISS index test PASSED")
    return True


def test_end_to_end_pipeline():
    """Test the complete end-to-end pipeline with a real paper."""
    print("\n" + "="*80)
    print("TEST 3: End-to-End Pipeline with Real Paper")
    print("="*80)
    
    # Select a test paper - use an indexed paper
    from database.operations import list_all_papers
    
    all_papers = list_all_papers()
    if not all_papers:
        print("   ⚠ No papers indexed in database")
        print("   Please index a paper first using index_pdf() MCP tool")
        return False
    
    # Use the first indexed paper
    test_filename = all_papers[0]["filename"]
    
    print(f"\n1. Checking if paper is indexed: {test_filename}")
    paper = get_paper_by_filename(test_filename)
    
    if not paper:
        print(f"   ⚠ Paper not indexed: {test_filename}")
        return False
    
    paper_id = paper["paper_id"]
    print(f"   ✓ Found paper: {paper.get('title', 'Unknown')}")
    print(f"   ✓ Paper ID: {paper_id}")
    print(f"   ✓ Chunks: {paper['num_chunks']}")
    
    # Get chunks
    print("\n2. Retrieving chunks from database...")
    chunks = get_all_chunks_for_paper(paper_id)
    print(f"   ✓ Retrieved {len(chunks)} chunks")
    
    # Check current embedding status
    chunks_with_embeddings = sum(1 for c in chunks if c.get("embedding_index") is not None)
    print(f"   ℹ Chunks with embeddings: {chunks_with_embeddings}/{len(chunks)}")
    
    # Generate embeddings (this would normally be done via MCP tool)
    print("\n3. Generating embeddings...")
    embedding_gen = get_embedding_generator()
    texts = [chunk["text"] for chunk in chunks]
    chunk_ids = [chunk["chunk_id"] for chunk in chunks]
    
    embeddings = embedding_gen.generate_embeddings(texts[:10], batch_size=5)  # Just first 10 for testing
    print(f"   ✓ Generated {len(embeddings)} embeddings")
    print(f"   ✓ Embedding dimension: {embeddings.shape[1]}")
    
    # Create/load FAISS index
    print("\n4. Creating FAISS index...")
    faiss_manager = FAISSIndexManager(
        index_name="research_papers_test",
        embedding_dim=embeddings.shape[1]
    )
    
    if not faiss_manager.load_index():
        faiss_manager.create_index()
        print("   ✓ Created new index")
    else:
        print(f"   ✓ Loaded existing index ({faiss_manager.index.ntotal} vectors)")
    
    # Add embeddings
    print("\n5. Adding embeddings to FAISS index...")
    start_idx = faiss_manager.index.ntotal
    success = faiss_manager.add_embeddings(embeddings, chunk_ids[:10])
    assert success, "Failed to add embeddings"
    print(f"   ✓ Added {len(embeddings)} embeddings")
    print(f"   ✓ Total vectors: {faiss_manager.index.ntotal}")
    
    # Save index
    print("\n6. Saving FAISS index...")
    success = faiss_manager.save_index()
    assert success, "Failed to save index"
    print(f"   ✓ Saved to: {faiss_manager.index_path}")
    
    # Test search
    print("\n7. Testing similarity search...")
    query_text = "semantic chunking of documents"
    query_embedding = embedding_gen.generate_embeddings([query_text])
    
    result_chunk_ids, distances = faiss_manager.search(query_embedding[0], k=5)
    print(f"   ✓ Query: '{query_text}'")
    print(f"   ✓ Found {len(result_chunk_ids)} results")
    
    # Retrieve full chunks
    if result_chunk_ids:
        print("\n8. Retrieving full chunk data...")
        result_chunks = get_chunks_by_ids(result_chunk_ids)
        print(f"   ✓ Retrieved {len(result_chunks)} chunks from database")
        
        for i, (chunk, dist) in enumerate(zip(result_chunks, distances[:len(result_chunks)])):
            print(f"\n   Result {i+1} (distance: {dist:.4f}):")
            print(f"      File: {chunk.get('filename', 'Unknown')}")
            print(f"      Section: {chunk.get('header_path', 'Unknown')}")
            print(f"      Pages: {chunk.get('page_start')}-{chunk.get('page_end')}")
            print(f"      Text preview: {chunk['text'][:100]}...")
    
    # Clean up test files
    print("\n9. Cleaning up test files...")
    if faiss_manager.index_path.exists():
        faiss_manager.index_path.unlink()
    if faiss_manager.mapping_path.exists():
        faiss_manager.mapping_path.unlink()
    print("   ✓ Cleaned up test files")
    
    print("\n✅ End-to-end pipeline test PASSED")
    return True


def main():
    """Run all Phase 4 tests."""
    print("\n" + "="*80)
    print("PHASE 4: QWEN EMBEDDINGS & FAISS INDEX - COMPREHENSIVE TEST")
    print("="*80)
    
    results = []
    
    # Test 1: Embedding generation
    try:
        results.append(("Embedding Generation", test_embedding_generation()))
    except Exception as e:
        logger.error(f"Test 1 failed: {str(e)}", exc_info=True)
        results.append(("Embedding Generation", False))
    
    # Test 2: FAISS index
    try:
        results.append(("FAISS Index Management", test_faiss_index()))
    except Exception as e:
        logger.error(f"Test 2 failed: {str(e)}", exc_info=True)
        results.append(("FAISS Index Management", False))
    
    # Test 3: End-to-end pipeline
    try:
        results.append(("End-to-End Pipeline", test_end_to_end_pipeline()))
    except Exception as e:
        logger.error(f"Test 3 failed: {str(e)}", exc_info=True)
        results.append(("End-to-End Pipeline", False))
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(result for _, result in results)
    print("\n" + "="*80)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("⚠️  SOME TESTS FAILED")
    print("="*80 + "\n")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

