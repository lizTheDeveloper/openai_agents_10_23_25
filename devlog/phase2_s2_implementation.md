# Phase 2 Extension: S2 Chunking Implementation - Implementation Log

## Date: 2025-10-31

## Overview
Extended Phase 2 to implement the S2 chunking algorithm from the paper "S2 Chunking: A Hybrid Framework for Document Segmentation Through Integrated Spatial and Semantic Analysis". Reorganized codebase into modular structure.

## Code Reorganization

### New Module Structure
```
.
├── semantic_chunked_pdf_rag.py  # MCP server (tools only)
├── pdf_processing/
│   ├── __init__.py
│   ├── validator.py             # PDF content validation
│   └── extractor.py             # Text extraction with layout analysis
├── chunking/
│   ├── __init__.py
│   ├── header_based.py          # Header-based chunking
│   └── s2_chunking.py           # S2 spatial-semantic chunking
└── utils/
    ├── __init__.py
    └── logger.py                # Centralized logging
```

### Benefits of Modular Structure
- **Separation of Concerns**: Each module has a clear responsibility
- **Testability**: Easy to test individual components
- **Maintainability**: Changes isolated to specific modules
- **Reusability**: Modules can be imported independently

## S2 Chunking Implementation

### Algorithm Overview
Based on the paper, S2 chunking combines:
1. **Spatial proximity** - using bounding box coordinates
2. **Semantic similarity** - using text embeddings
3. **Spectral clustering** - to find natural groupings
4. **Token length constraints** - enforcing maximum chunk sizes

### Key Components

#### 1. Spatial Weight Calculation
```python
w_spatial(i,j) = 1 / (1 + distance(bbox_i, bbox_j))
```
- Uses Euclidean distance between bounding box centroids
- Closer elements get higher weights
- Captures physical layout relationships

#### 2. Semantic Weight Calculation
```python
w_semantic(i,j) = cosine_similarity(embedding_i, embedding_j)
```
- Uses sentence-transformers (all-MiniLM-L6-v2 model)
- Embeddings normalized for efficient cosine similarity
- Captures meaning and context

#### 3. Combined Weights
```python
w_combined(i,j) = (w_spatial(i,j) + w_semantic(i,j)) / 2
```
- Simple average of spatial and semantic weights
- Creates affinity matrix for clustering

#### 4. Spectral Clustering
- Dynamic cluster count estimation based on token limits
- Kmeans label assignment for final clustering
- Handles non-linear relationships in document structure

#### 5. Token Length Enforcement
- Splits oversized clusters at paragraph boundaries
- Ensures no chunk exceeds max_token_length
- Character-based approximation (1 token ≈ 4 characters)

### Dependencies Added
- `scikit-learn` (1.7.2) - Spectral clustering
- `sentence-transformers` (5.1.2) - Text embeddings
- `torch` (2.9.0) - Neural network backend
- `numpy` (2.3.4) - Matrix operations

## Testing Results

### Test PDF: `2501.05485v1.pdf` (10 pages, 124 segments)

**Header-Based Chunking:**
- Chunks created: 52
- Average size: 331 characters
- Method: Splits at structural boundaries (headers)
- Preserves document hierarchy

**S2 Chunking:**
- Chunks created: 15
- Average size: 1,153 characters  
- Method: Clusters by spatial+semantic similarity
- Token limit: 512 tokens (~2,048 characters)

### Comparison
| Metric | Header-Based | S2 Chunking |
|--------|-------------|-------------|
| Chunks | 52 | 15 |
| Avg Size | 331 chars | 1,153 chars |
| Respects Structure | ✓ | ~ |
| Semantic Coherence | ~ | ✓ |
| Spatial Awareness | ✗ | ✓ |
| Token Control | ✗ | ✓ |

## MCP Tool Updates

### Enhanced `chunk_pdf` Tool
```python
chunk_pdf(filename: str, method: str = "header") -> dict
```

**New Features:**
- `method` parameter: Choose "header" or "s2"
- Returns chunking method in response
- Same response format for both methods
- Performance metrics logged per method

**Example Usage:**
```python
# Header-based chunking
result = chunk_pdf("paper.pdf", method="header")

# S2 chunking
result = chunk_pdf("paper.pdf", method="s2")
```

## Performance Characteristics

### Header-Based Chunking
- ✓ **Fast**: No embedding generation needed
- ✓ **Deterministic**: Same results every time
- ✓ **Structure-aware**: Maintains document hierarchy
- ✗ **Size variation**: Chunks can be very small or large
- ✗ **No semantic awareness**: May split related content

### S2 Chunking
- ✓ **Semantic coherence**: Groups related content
- ✓ **Spatial awareness**: Considers layout relationships
- ✓ **Controlled size**: Enforces token limits
- ✗ **Slower**: Embedding generation + clustering
- ✗ **Non-deterministic**: Clustering may vary slightly
- ✗ **Memory intensive**: Affinity matrix is O(n²)

## Use Case Recommendations

**Use Header-Based when:**
- Document has clear hierarchical structure
- Need to preserve exact document organization
- Speed is critical
- Working with very large documents

**Use S2 when:**
- Need semantically coherent chunks
- Document has complex multi-column layout
- Token limits are critical (e.g., LLM context windows)
- Want to capture spatial relationships (figures with captions)

## Known Limitations

### S2 Chunking
1. **Memory Usage**: O(n²) affinity matrix for n segments
2. **Computation Time**: ~3 seconds for 124 segments (includes model loading)
3. **Model Loading**: First run loads sentence-transformers model (~100MB)
4. **Token Estimation**: Character-based approximation not exact

### Both Methods
1. **No cross-page awareness**: Chunks respect page boundaries
2. **Text-only**: Images and tables not processed
3. **No heading preservation**: S2 doesn't maintain header paths

## Next Steps (Phase 3)
- Design SQLite schema for storing chunks
- Add navigation indices (prev/next, section ranges)
- Implement database operations
- Store both chunking methods' results
- Add metadata for retrieval

## Notes
- S2 chunking model caching: Model loaded once per process
- Both methods work on same segment extraction pipeline
- Modular structure makes adding new chunking methods easy
- Performance metrics logged for both methods separately

