# Test Suite

This directory contains all test scripts for the PDF Research Paper Indexing MCP Server.

## Running Tests

All tests should be run from the project root with the virtual environment activated:

```bash
cd /Users/annhoward/openai_agents_10_23_25
source env/bin/activate
python tests/test_name.py
```

## Test Files

### Component Tests

#### `test_s2_chunking.py`
Tests the S2 (spatial-semantic) chunking algorithm.

**What it tests:**
- Spatial weight calculation
- Semantic weight calculation using embeddings
- Spectral clustering
- Token length enforcement
- Complete S2 chunking pipeline

**Dependencies:** scikit-learn, sentence-transformers

---

#### `test_phase3_database.py`
Tests Phase 3 database operations and models.

**What it tests:**
- Database schema creation
- Paper insertion and retrieval
- Chunk insertion with navigation indices
- Section creation and mapping
- Database queries and relationships

**Dependencies:** SQLAlchemy, SQLite

---

#### `test_phase4_embeddings.py`
Comprehensive test suite for Phase 4 embedding generation and FAISS indexing.

**What it tests:**
1. **Embedding Generation**
   - MLX model loading
   - Batch processing
   - Embedding normalization
   - Similarity computation

2. **FAISS Index Management**
   - Index creation and configuration
   - Embedding addition
   - Save/load persistence
   - Similarity search
   - Statistics and cleanup

3. **End-to-End Pipeline**
   - Database integration
   - Full paper embedding generation
   - FAISS index persistence
   - Search with real chunks
   - Metadata retrieval

**Dependencies:** mlx, mlx-embeddings, faiss-cpu

**Runtime:** ~30-60 seconds

---

#### `test_phase4_integration.py`
Integration test for the complete Phase 4 embedding pipeline.

**What it tests:**
- Complete workflow from database → embeddings → FAISS → search
- Persistence and reload verification
- Database update confirmation
- Semantic search functionality

**Dependencies:** mlx, mlx-embeddings, faiss-cpu

**Runtime:** ~5-10 seconds

---

#### `test_phase5_query_tools.py`
Tests Phase 5 query tools and search functionality.

**What it tests:**
1. **Semantic Search**
   - Query embedding generation
   - FAISS similarity search
   - Context window retrieval
   - Result ranking

2. **Document Section Retrieval**
   - By chunk index
   - By header path
   - By page range
   - Error handling

3. **End-to-End Search**
   - Full search pipeline
   - Context window expansion
   - Metadata enrichment

**Dependencies:** mlx, mlx-embeddings, faiss-cpu

**Runtime:** ~10-20 seconds

---

### MCP Integration Tests

#### `test_mcp_phase3.py`
Tests Phase 3 MCP tools (database indexing).

**What it tests:**
- `index_pdf()` tool
- `list_indexed_papers()` tool
- `get_document_structure()` tool

**Dependencies:** FastMCP

---

#### `test_mcp_integration.py`
Integration tests for all MCP tools across phases.

**What it tests:**
- Tool registration and availability
- Tool parameter validation
- Error handling
- Integration between tools

**Dependencies:** FastMCP

---

#### `test_mcp_live.py`
Live MCP server tests (requires running server).

**What it tests:**
- Server startup and initialization
- Tool invocation via MCP protocol
- Response formatting
- Error propagation

**Note:** This test requires the MCP server to be running.

**Dependencies:** FastMCP, MCP client

---

## Test Organization

```
tests/
├── README.md                          # This file
│
├── Component Tests
│   ├── test_s2_chunking.py           # S2 chunking algorithm
│   ├── test_phase3_database.py       # Database operations
│   ├── test_phase4_embeddings.py     # Embeddings & FAISS (comprehensive)
│   ├── test_phase4_integration.py    # Embeddings integration
│   └── test_phase5_query_tools.py    # Query tools
│
└── Integration Tests
    ├── test_mcp_phase3.py            # Phase 3 MCP tools
    ├── test_mcp_integration.py       # Cross-phase integration
    └── test_mcp_live.py              # Live server tests
```

## Test Coverage

### Phase 1: MCP Foundation & PDF Download
- Tested via `test_mcp_integration.py`
- Manual testing with `download_pdf()` tool

### Phase 2: PDF Processing & Chunking
- Header-based: Tested via integration tests
- S2 chunking: `test_s2_chunking.py`

### Phase 3: Navigation Indexing & Metadata Storage
- `test_phase3_database.py` - Database operations
- `test_mcp_phase3.py` - MCP tool interface

### Phase 4: Embeddings & FAISS Index
- `test_phase4_embeddings.py` - Comprehensive suite (3 test categories)
- `test_phase4_integration.py` - Integration workflow

### Phase 5: Query Tools
- `test_phase5_query_tools.py` - Search and retrieval

## Running All Tests

To run all tests in sequence:

```bash
cd /Users/annhoward/openai_agents_10_23_25
source env/bin/activate

# Component tests
python tests/test_s2_chunking.py
python tests/test_phase3_database.py
python tests/test_phase4_embeddings.py
python tests/test_phase4_integration.py
python tests/test_phase5_query_tools.py

# Integration tests
python tests/test_mcp_phase3.py
python tests/test_mcp_integration.py
```

## Common Issues

### ImportError
Make sure you're running from the project root and the virtual environment is activated:
```bash
cd /Users/annhoward/openai_agents_10_23_25
source env/bin/activate
```

### Database Not Found
Some tests require papers to be indexed. Use the MCP tools to index a paper first:
```python
from semantic_chunked_pdf_rag import index_pdf
result = index_pdf("your_paper.pdf")
```

### FAISS Index Not Found
Phase 4 and 5 tests may create temporary indices. These are cleaned up automatically, but persistent indices may need to be created:
```python
from embeddings import get_embedding_generator, FAISSIndexManager
# See test files for examples
```

## Test Data

Tests use the following data sources:
- Papers in `./papers/` directory
- Database at `./indexes/research_papers.db`
- FAISS indices at `./indexes/research_papers.faiss`

Some tests create temporary test files that are cleaned up automatically.

## Adding New Tests

When adding new tests:
1. Place in `tests/` directory
2. Name with `test_` prefix
3. Add documentation to this README
4. Include cleanup code to remove temporary files
5. Make tests idempotent (can run multiple times)

## CI/CD

These tests can be integrated into CI/CD pipelines. Consider:
- Running tests in isolated environments
- Mocking external dependencies
- Caching model downloads
- Parallel test execution where possible

