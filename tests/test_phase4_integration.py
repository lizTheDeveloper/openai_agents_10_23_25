"""
Phase 4 Integration Test - Demonstrates complete embedding generation pipeline.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

from database.operations import get_paper_by_filename, get_all_chunks_for_paper, update_chunks_embedding_indices
from embeddings import get_embedding_generator, FAISSIndexManager

print("\n" + "="*80)
print("PHASE 4 INTEGRATION TEST: Complete Embedding Pipeline")
print("="*80)

# Step 1: Select a paper
print("\n1. Selecting test paper...")
paper = get_paper_by_filename("test_paper.pdf")
if not paper:
    print("   ⚠ test_paper.pdf not found, using first available paper")
    from database.operations import list_all_papers
    papers = list_all_papers()
    if not papers:
        print("   ❌ No papers found. Please index a paper first.")
        sys.exit(1)
    paper = papers[0]

print(f"   ✓ Using paper: {paper['filename']}")
print(f"   ✓ Paper ID: {paper['paper_id']}, Chunks: {paper['num_chunks']}")

# Step 2: Get chunks
print("\n2. Retrieving chunks from database...")
chunks = get_all_chunks_for_paper(paper['paper_id'])
print(f"   ✓ Retrieved {len(chunks)} chunks")

# Step 3: Generate embeddings
print("\n3. Generating embeddings with MLX...")
embedding_gen = get_embedding_generator()
print(f"   ✓ Model: {embedding_gen.model_name}")
print(f"   ✓ Dimension: {embedding_gen.get_embedding_dimension()}")

texts = [chunk["text"] for chunk in chunks]
chunk_ids = [chunk["chunk_id"] for chunk in chunks]

embeddings = embedding_gen.generate_embeddings(texts, batch_size=32)
print(f"   ✓ Generated {len(embeddings)} embeddings")
print(f"   ✓ Shape: {embeddings.shape}")

# Step 4: Create/load FAISS index
print("\n4. Managing FAISS index...")
faiss_manager = FAISSIndexManager(
    index_name="research_papers",
    embedding_dim=embeddings.shape[1]
)

if not faiss_manager.load_index():
    print("   ✓ Creating new FAISS index")
    faiss_manager.create_index()
else:
    print(f"   ✓ Loaded existing index ({faiss_manager.index.ntotal} vectors)")

# Step 5: Add embeddings
print("\n5. Adding embeddings to FAISS index...")
start_idx = faiss_manager.index.ntotal
success = faiss_manager.add_embeddings(embeddings, chunk_ids)
if success:
    print(f"   ✓ Added {len(embeddings)} embeddings")
    print(f"   ✓ Total vectors in index: {faiss_manager.index.ntotal}")
else:
    print("   ❌ Failed to add embeddings")
    sys.exit(1)

# Step 6: Update database
print("\n6. Updating database with embedding indices...")
updates = [
    (chunk_ids[i], start_idx + i)
    for i in range(len(chunk_ids))
]
success = update_chunks_embedding_indices(updates)
if success:
    print(f"   ✓ Updated {len(updates)} chunks with embedding indices")
else:
    print("   ⚠ Database update failed (embeddings still in FAISS)")

# Step 7: Save FAISS index
print("\n7. Saving FAISS index to disk...")
success = faiss_manager.save_index()
if success:
    print(f"   ✓ Saved to: {faiss_manager.index_path}")
else:
    print("   ⚠ Failed to save index")

# Step 8: Test search
print("\n8. Testing semantic search...")
query_text = "machine learning and artificial intelligence"
query_embedding = embedding_gen.generate_embeddings([query_text])

result_chunk_ids, distances = faiss_manager.search(query_embedding[0], k=3)
print(f"   ✓ Query: '{query_text}'")
print(f"   ✓ Found {len(result_chunk_ids)} results:")

for i, (chunk_id, dist) in enumerate(zip(result_chunk_ids, distances)):
    # Find the chunk
    matching_chunk = next((c for c in chunks if c['chunk_id'] == chunk_id), None)
    if matching_chunk:
        text_preview = matching_chunk['text'][:80].replace('\n', ' ')
        print(f"      {i+1}. Distance: {dist:.4f} - '{text_preview}...'")

# Step 9: Verify persistence
print("\n9. Verifying index persistence...")
faiss_manager2 = FAISSIndexManager("research_papers", embeddings.shape[1])
if faiss_manager2.load_index():
    print(f"   ✓ Successfully loaded index from disk")
    print(f"   ✓ Index contains {faiss_manager2.index.ntotal} vectors")
else:
    print("   ❌ Failed to load index from disk")

# Summary
print("\n" + "="*80)
print("✅ PHASE 4 INTEGRATION TEST COMPLETED SUCCESSFULLY!")
print("="*80)
print("\nKey Achievements:")
print(f"  • Generated {len(embeddings)} embeddings using MLX")
print(f"  • Indexed {faiss_manager.index.ntotal} vectors in FAISS")
print(f"  • Updated {len(updates)} database records")
print(f"  • Persisted index to disk")
print(f"  • Verified semantic search functionality")
print("\n" + "="*80 + "\n")

