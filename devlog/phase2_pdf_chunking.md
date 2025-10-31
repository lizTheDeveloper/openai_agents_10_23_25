# Phase 2: PDF Processing & Header-Based Chunking - Implementation Log

## Date: 2025-01-30

## Overview
Phase 2 focuses on implementing PDF text extraction with header detection and semantic chunking. This phase enables the system to parse PDF documents, identify structural elements (headers), and chunk content semantically based on document hierarchy.

## Completed Tasks

### 1. PDF Text Extraction with PyMuPDF
- Integrated PyMuPDF (fitz) for PDF text extraction with layout analysis
- Implemented `extract_text_with_headers()` function that:
  - Extracts text blocks from PDF pages using `get_text("dict")`
  - Preserves layout information (font size, font name, position)
  - Analyzes each text span for header characteristics
  - Returns structured segments with metadata (page, font info, header status)

### 2. Font Size Analysis
- Implemented `calculate_common_font_size()` function:
  - Scans all pages to collect font sizes
  - Uses Counter to identify the most common font size (body text)
  - Provides baseline for header detection heuristics

### 3. Header Detection Algorithm
- Implemented `is_likely_header()` function with multi-factor analysis:
  - **Font size ratio**: Compares span font size to document's common font size
  - **Font style**: Detects bold text (via flags or font name patterns like "CMBX12")
  - **Text patterns**: Matches academic paper section patterns (Abstract, Introduction, etc.)
  - **Position analysis**: Left-aligned text (< 100px) more likely to be headers
  - **Text characteristics**: Short text (< 100 chars) more likely to be headers
  
- **Header level assignment**:
  - Level 1: Main sections (size ratio > 1.5, or > 1.2 with bold)
  - Level 2: Subsections (size ratio > 1.1, or bold)
  - Level 3: Subsubsections (size ratio >= 1.0, or bold + left-aligned)

### 4. Header Path Construction
- Implemented `build_header_path()` function:
  - Maintains header hierarchy stack as document is processed
  - Builds full path strings like "1. Introduction > 1.1. Background"
  - Handles header level transitions (pop stack when going up hierarchy)
  - Strips numeric prefixes for cleaner path strings

### 5. Semantic Chunking Logic
- Implemented `chunk_pdf_by_headers()` function:
  - Groups content under header boundaries
  - Splits chunks when encountering headers of same or higher level
  - Preserves header hierarchy in chunk metadata
  - Tracks page ranges for each chunk (page_start, page_end)
  - Assigns sequential 0-based chunk indices

### 6. PDF Content Validation Fix
- Fixed `validate_pdf_content()` function:
  - Corrected misleading comment about PDF header format
  - Now properly checks for "%PDF-" (5 bytes) as primary validation
  - Falls back to 4-byte check for compatibility
  - More accurate validation of actual PDF file format

### 7. MCP Tool Implementation
- Added `chunk_pdf()` MCP tool:
  - Accepts filename from ./papers/ directory
  - Validates file existence and PDF format
  - Performs full extraction → chunking pipeline
  - Returns structured response with:
    - `num_chunks`: Total number of chunks created
    - `chunks`: List of chunk dictionaries with:
      - `chunk_index`: 0-based sequential index
      - `text`: Chunk content (truncated to 1000 chars in response)
      - `full_text_length`: Full text length
      - `header_path`: Full header hierarchy path
      - `page_start`: First page (0-indexed)
      - `page_end`: Last page (0-indexed)
      - `header_level`: Header level (1-3) or 0 for non-header content
  - Comprehensive error handling and logging
  - Performance metrics logging

### 8. Dependencies
- Installed PyMuPDF (pymupdf-1.26.5)
- Verified compatibility with existing FastMCP and httpx dependencies

## Code Structure

### New Functions Added

```
semantic_chunked_pdf_rag.py
├── calculate_common_font_size(doc: fitz.Document) -> float
├── is_likely_header(...) -> Tuple[bool, int]
├── extract_text_with_headers(doc: fitz.Document) -> List[Dict]
├── build_header_path(segments, current_index) -> str
├── chunk_pdf_by_headers(segments) -> List[Dict]
└── chunk_pdf(filename: str) -> dict  # MCP tool
```

## Testing Results

### Test PDF: `2501.05485v1.pdf` (10 pages)
- ✓ PDF validation successful
- ✓ Extracted 124 text segments
- ✓ Created 52 semantic chunks
- ✓ Header detection working (identifies sections, subsections)
- ✓ Header paths constructed correctly
- ✓ Page tracking accurate

### Sample Chunk Structure
```python
{
    "chunk_index": 5,
    "text": "1 Introduction...",
    "header_path": "1 Introduction",
    "page_start": 0,
    "page_end": 0,
    "header_level": 1
}
```

## Key Features

1. **Layout-Aware Extraction**: Uses PyMuPDF's layout analysis to preserve spatial relationships
2. **Multi-Factor Header Detection**: Combines font size, style, position, and text patterns
3. **Hierarchical Chunking**: Maintains document structure through header paths
4. **Page Tracking**: Each chunk knows its page range for navigation
5. **Robust Error Handling**: Validates PDFs, handles edge cases, logs errors

## Known Limitations

1. **Header Detection Sensitivity**: May occasionally treat author names or dates as headers (over-inclusive approach)
2. **Multi-Column Layouts**: May need enhancement for complex multi-column documents
3. **Font Name Variations**: Header detection relies on common LaTeX font patterns (CMBX, CMR, etc.)

## Next Steps (Phase 3)
- Design SQLite schema for chunk storage
- Implement database operations (create, insert, query)
- Add navigation indices (prev/next chunk links)
- Build section boundary tracking

## Notes
- Chunking preserves full document structure through header paths
- Text is extracted with line breaks preserved where relevant
- Header detection is intentionally over-inclusive to avoid missing real sections
- Performance: ~52 chunks from 10-page PDF in < 1 second

