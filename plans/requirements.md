# PDF Research Paper Indexing MCP Server - Requirements

## Overview
An MCP (Model Context Protocol) server that enables AI agents to access and query research papers by downloading PDFs from URLs, semantically chunking them based on headers, indexing them with FAISS, and using Qwen 0.6 embeddings for semantic search.

## Core Requirements

### 1. MCP Server Structure
- **Framework**: FastMCP (as seen in existing `semantic_chunked_pdf_rag.py`)
- **Transport**: stdio (standard input/output) for MCP communication
- **Server Name**: "PDF Research Paper Indexer" or similar descriptive name

### 2. PDF Download Functionality
- **Tool**: `download_pdf`
  - **Input**: URL (string) of a PDF document
  - **Behavior**:
    - Downloads PDF from the provided URL
    - Validates that the URL points to a valid PDF file
    - Saves the PDF to a designated local storage directory (e.g., `./papers/`)
    - Returns success status and local file path
    - Handles errors gracefully (network errors, invalid URLs, non-PDF content)
  - **Dependencies**: 
    - `httpx` for async HTTP downloads
    - File system operations for saving

### 3. Semantic Chunking Based on Headers
- **Tool**: `chunk_pdf_by_headers` (or integrated into download/indexing process)
  - **Input**: Local PDF file path or URL
  - **Behavior**:
    - Extracts text from PDF
    - Identifies headers and subheaders using:
      - Font size analysis
      - Font style analysis (bold, italics)
      - Structural analysis (document outline)
      - Heuristics for common academic paper structures
    - Chunks text semantically at header boundaries
    - Preserves header hierarchy information
    - Maintains context (chunks include their parent headers)
    - **Document Navigation Setup**:
      - Assigns sequential chunk indices (0-based) for each paper
      - Creates bidirectional links (prev_chunk_index, next_chunk_index)
      - Maps chunks to document sections (section_start_chunk, section_end_chunk)
      - Indexes header paths for section-based retrieval
    - Returns structured chunks with metadata:
      - Chunk text content
      - Header path (e.g., "Introduction > Background")
      - Page number
      - Chunk index (for navigation)
      - Navigation indices (prev/next, section boundaries)
  - **Dependencies**:
    - `PyMuPDF` (fitz) for high-performance PDF text extraction with font/layout analysis
    - Optional: `unstructured` for advanced semantic element detection (headings, paragraphs, tables)

### 4. Embedding Generation with Qwen 0.6
- **Model**: Qwen 0.6 embedding model
- **Behavior**:
  - Generates embeddings for each semantic chunk
  - Handles batch processing for efficiency
  - Supports local deployment of Qwen 0.6
  - Ensures embeddings are compatible with FAISS indexing
- **Dependencies**:
  - `mlx` - MLX framework for Apple Silicon
  - `mlx-lm` - MLX language models library for Qwen 0.6 inference
  - Model files for Qwen 0.6 embedding model (downloaded from HuggingFace or MLX format)
  - Note: MLX optimized for Apple Silicon (M-series chips), no separate GPU package needed

### 5. FAISS Indexing
- **Index Type**: FAISS (Facebook AI Similarity Search)
- **Behavior**:
  - Creates a FAISS index from generated embeddings
  - Stores index persistently on disk
  - Maintains metadata mapping (embedding index → chunk, paper, header path)
  - Supports incremental indexing (adding new papers to existing index)
  - Handles index updates and versioning
  - **Document Navigation Support**:
    - Maintains chunk ordering within each paper
    - Stores bidirectional chunk references (prev/next chunk indices)
    - Indexes chunk positions relative to document sections
    - Enables efficient retrieval of neighboring chunks
- **Storage**:
  - Index file: `./indexes/research_papers.faiss`
  - Metadata database: SQLite database (preferred) or JSON file
    - Chunk table with navigation indices
    - Paper table with structure metadata
    - Header/section mapping table
- **Dependencies**:
  - `faiss-cpu` for FAISS operations (compatible with MLX numpy arrays)
  - `numpy` for array operations (MLX-compatible)
  - `sqlite3` (built-in Python) for synchronous database operations
  - Optional: `aiosqlite` if async database operations needed

### 6. Query Interface
- **Tool**: `search_research_papers`
  - **Input**: 
    - Query string (required)
    - `include_context` (optional, default: true) - Whether to include neighboring chunks
    - `context_window` (optional, default: 1) - Number of chunks before and after to include
    - `top_k` (optional, default: 5) - Number of top results to return
  - **Behavior**:
    - Generates embedding for the query using Qwen 0.6
    - Performs similarity search in FAISS index
    - For each matched chunk:
      - Returns the matched chunk text with metadata
      - If `include_context` is true, includes `context_window` chunks before and after the matched chunk
      - Provides document navigation indices for progressive loading
    - Returns results with:
      - **Matched chunk**: The chunk that matched the query
        - Chunk text
        - Source paper filename/URL
        - Header path
        - Similarity score
        - Page number
        - Chunk index (for navigation)
      - **Context chunks** (if `include_context` is true):
        - Previous chunk(s) text and metadata
        - Next chunk(s) text and metadata
      - **Document reference**: Index and position information for deeper exploration
- **Tool**: `get_document_section`
  - **Input**: 
    - `paper_id` or `paper_url` (required)
    - `chunk_index` (optional) - Starting chunk index
    - `header_path` (optional) - Header path to retrieve section
    - `num_chunks` (optional, default: 1) - Number of consecutive chunks to retrieve
    - `start_page` and `end_page` (optional) - Page range to retrieve
  - **Behavior**:
    - Retrieves specific section(s) of a document by:
      - Chunk index range (e.g., chunks 5-10)
      - Header path (e.g., "Introduction > Background")
      - Page range (e.g., pages 3-5)
    - Returns full chunk text with complete metadata
    - Enables progressive loading of document sections
    - Maintains document structure and hierarchy
- **Tool**: `get_document_structure`
  - **Input**: `paper_id` or `paper_url` (required)
  - **Behavior**:
    - Returns document outline/structure:
      - Header hierarchy
      - Chunk indices per section
      - Page ranges per section
      - Total chunks and pages
    - Provides navigation index for the document
- **Tool**: `list_indexed_papers`
  - **Input**: None
  - **Behavior**:
    - Returns list of all papers that have been indexed
    - Includes metadata: URL, download date, number of chunks

### 7. Integration with AI Agents
- MCP server must expose tools that AI agents can discover and call
- Tools should have clear descriptions and type hints
- Server should be accessible via MCP protocol (stdio transport)
- Error handling should provide meaningful messages to agents

## Technical Specifications

### Directory Structure
```
.
├── papers/              # Downloaded PDF files
│   └── [paper_name].pdf
├── indexes/             # FAISS index and metadata
│   ├── research_papers.faiss
│   └── research_papers_metadata.json
├── semantic_chunked_pdf_rag.py  # Main MCP server
└── plans/
    └── requirements.md
```

### Data Model

#### Chunk Metadata Structure
```python
{
    "chunk_id": str,
    "paper_id": str,
    "paper_url": str,
    "paper_filename": str,
    "header_path": str,  # e.g., "1. Introduction > 1.1 Background"
    "chunk_text": str,
    "page_number": int,
    "chunk_index": int,  # Order within paper (0-based for navigation)
    "embedding_index": int,  # Index in FAISS
    "prev_chunk_index": Optional[int],  # Previous chunk index (None if first)
    "next_chunk_index": Optional[int],  # Next chunk index (None if last)
    "section_start_chunk": int,  # First chunk in this header section
    "section_end_chunk": int  # Last chunk in this header section
}
```

#### Paper Metadata Structure
```python
{
    "paper_id": str,
    "url": str,
    "filename": str,
    "download_date": datetime,
    "num_chunks": int,
    "title": str  # If extractable from PDF
}
```

### Performance Requirements
- PDF download: Should handle files up to 50MB
- Chunking: Should process papers up to 100 pages efficiently
- Embedding generation: Should support batch processing
- Indexing: Should handle incremental additions without rebuilding entire index
- Query response: Should return results in < 1 second for typical queries

### Error Handling
- Network errors during PDF download
- Invalid PDF format
- Missing or corrupted index files
- Embedding generation failures
- FAISS indexing errors
- All errors should be logged and returned with meaningful messages

## Dependencies

### Python Packages
- `fastmcp` - MCP server framework
- `httpx` - HTTP client for downloads (async support)
- `PyMuPDF` (imported as `fitz`) - High-performance PDF text extraction with layout analysis
- `mlx` - MLX framework for Apple Silicon
- `mlx-lm` - MLX language models (for Qwen embedding model inference)
- `faiss-cpu` - FAISS indexing (CPU-only, compatible with MLX embeddings)
- `numpy` - Array operations (MLX-compatible)
- `sqlite3` (built-in) or `aiosqlite` - SQLite database for metadata storage
- `unstructured` (optional) - Advanced semantic chunking with heading detection

### System Requirements
- Python 3.13 (based on existing virtual environment)
- Sufficient disk space for papers and indexes
- RAM: Sufficient for embedding model and FAISS index (64GB available per user info)
- Optional: GPU support for faster embedding generation

## Future Enhancements (Out of Scope for Initial Version)
- Multi-format support (epub, docx)
- Automatic paper metadata extraction (authors, abstract, citations)
- Citation graph building
- Deduplication of similar papers
- Full-text search alongside semantic search
- Web interface for paper management
- Automatic paper discovery and download

## Testing Requirements
- Unit tests for PDF downloading
- Unit tests for header detection and chunking
- Unit tests for embedding generation
- Integration tests for full pipeline (download → chunk → embed → index → query)
- Test with various PDF formats (single-column, multi-column, scanned)
- Test with papers of different lengths and structures

## Logging
- Implement centralized logging module
- Log all operations: downloads, chunking, indexing, queries
- Log errors with full context
- Log performance metrics

## Progressive Context Loading Strategy

### Query Response Design
When a query matches a chunk, the system should:
1. **Primary Match**: Return the matched chunk with high relevance
2. **Contextual Neighbors**: Include adjacent chunks (default: 1 before, 1 after) to provide context
3. **Document Reference**: Provide indices and navigation information for deeper exploration
4. **Progressive Loading**: Enable agents to request additional chunks on-demand using document indices

### Use Cases
- **Initial Search**: Agent queries, gets matched chunk + neighbors
- **Context Expansion**: If initial chunk is relevant but needs more context, agent can request surrounding chunks using `get_document_section`
- **Section Navigation**: Agent can navigate entire sections using header paths
- **Document Browsing**: Agent can explore full document structure using `get_document_structure`

### Benefits
- Reduces initial response size while providing immediate context
- Allows agents to progressively load more information as needed
- Enables both semantic search and structured document navigation
- Supports natural conversation flow where agents explore documents iteratively

## Notes
- User reads many research papers and wants AI agents to access them
- System should be designed for incremental addition of papers
- Index should persist between server restarts
- Use SQLite for metadata storage to support efficient chunk navigation queries
- Document indices enable efficient retrieval without full document loading
- Progressive loading reduces memory usage while maintaining context availability

