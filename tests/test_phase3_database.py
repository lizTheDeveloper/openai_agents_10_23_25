"""
Integration test for Phase 3: Database indexing and navigation.

Tests:
1. Database initialization
2. Paper insertion
3. Chunk insertion with navigation indices
4. Section creation
5. Query operations
"""
import os
import sys
from pathlib import Path
import fitz

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from database.operations import (
    initialize_database,
    insert_paper,
    insert_chunks,
    insert_sections,
    get_paper_by_filename,
    get_chunk,
    get_chunks_range,
    get_section,
    list_all_papers,
    get_paper_structure
)
from pdf_processing import extract_text_with_headers
from chunking import chunk_by_headers
from utils.logger import get_logger

logger = get_logger()

def test_database_initialization():
    """Test database initialization."""
    print("\n=== Test 1: Database Initialization ===")
    
    # Remove existing database if present (for clean test)
    project_root = Path(__file__).parent.absolute()
    db_path = project_root / "indexes" / "research_papers.db"
    if db_path.exists():
        os.remove(db_path)
        print(f"Removed existing database: {db_path}")
    
    result = initialize_database()
    assert result, "Database initialization failed"
    assert db_path.exists(), "Database file was not created"
    print("✅ Database initialized successfully")


def test_paper_insertion():
    """Test inserting a paper into the database."""
    print("\n=== Test 2: Paper Insertion ===")
    
    paper_id = insert_paper(
        url="https://example.com/test_paper.pdf",
        filename="test_paper.pdf",
        title="Test Paper Title",
        num_pages=10,
        chunking_method="header"
    )
    
    assert paper_id is not None, "Failed to insert paper"
    assert paper_id > 0, "Invalid paper_id returned"
    print(f"✅ Paper inserted with paper_id: {paper_id}")
    
    # Verify we can retrieve the paper
    paper = get_paper_by_filename("test_paper.pdf")
    assert paper is not None, "Failed to retrieve inserted paper"
    assert paper["paper_id"] == paper_id, "Retrieved paper has wrong ID"
    assert paper["title"] == "Test Paper Title", "Retrieved paper has wrong title"
    print(f"✅ Paper retrieved successfully: {paper}")
    
    return paper_id


def test_chunk_insertion(paper_id):
    """Test inserting chunks with navigation indices."""
    print("\n=== Test 3: Chunk Insertion with Navigation ===")
    
    # Create test chunks
    test_chunks = [
        {
            "chunk_index": 0,
            "text": "Introduction section text here...",
            "header_path": "Introduction",
            "header_level": 1,
            "page_start": 0,
            "page_end": 1
        },
        {
            "chunk_index": 1,
            "text": "Background subsection text here...",
            "header_path": "Introduction > Background",
            "header_level": 2,
            "page_start": 1,
            "page_end": 2
        },
        {
            "chunk_index": 2,
            "text": "Methods section text here...",
            "header_path": "Methods",
            "header_level": 1,
            "page_start": 3,
            "page_end": 5
        }
    ]
    
    result = insert_chunks(paper_id, test_chunks)
    assert result, "Failed to insert chunks"
    print(f"✅ Inserted {len(test_chunks)} chunks")
    
    # Verify navigation indices
    chunk_0 = get_chunk(paper_id, 0)
    assert chunk_0 is not None, "Failed to retrieve chunk 0"
    assert chunk_0["prev_chunk_index"] is None, "First chunk should have no previous"
    assert chunk_0["next_chunk_index"] == 1, "First chunk should point to chunk 1"
    print(f"✅ Chunk 0 navigation: prev={chunk_0['prev_chunk_index']}, next={chunk_0['next_chunk_index']}")
    
    chunk_1 = get_chunk(paper_id, 1)
    assert chunk_1 is not None, "Failed to retrieve chunk 1"
    assert chunk_1["prev_chunk_index"] == 0, "Middle chunk should point to chunk 0"
    assert chunk_1["next_chunk_index"] == 2, "Middle chunk should point to chunk 2"
    print(f"✅ Chunk 1 navigation: prev={chunk_1['prev_chunk_index']}, next={chunk_1['next_chunk_index']}")
    
    chunk_2 = get_chunk(paper_id, 2)
    assert chunk_2 is not None, "Failed to retrieve chunk 2"
    assert chunk_2["prev_chunk_index"] == 1, "Last chunk should point to chunk 1"
    assert chunk_2["next_chunk_index"] is None, "Last chunk should have no next"
    print(f"✅ Chunk 2 navigation: prev={chunk_2['prev_chunk_index']}, next={chunk_2['next_chunk_index']}")
    
    # Test range retrieval
    chunk_range = get_chunks_range(paper_id, 0, 2)
    assert len(chunk_range) == 3, "Should retrieve 3 chunks"
    assert chunk_range[0]["chunk_index"] == 0, "First chunk should be index 0"
    assert chunk_range[2]["chunk_index"] == 2, "Last chunk should be index 2"
    print(f"✅ Retrieved chunk range [0-2]: {len(chunk_range)} chunks")
    
    return test_chunks


def test_section_insertion(paper_id, chunks):
    """Test section creation and retrieval."""
    print("\n=== Test 4: Section Insertion ===")
    
    result = insert_sections(paper_id, chunks)
    assert result, "Failed to insert sections"
    print("✅ Sections inserted successfully")
    
    # Verify section retrieval
    intro_section = get_section(paper_id, "Introduction")
    assert intro_section is not None, "Failed to retrieve Introduction section"
    assert intro_section["start_chunk_index"] == 0, "Introduction should start at chunk 0"
    print(f"✅ Introduction section: chunks {intro_section['start_chunk_index']}-{intro_section['end_chunk_index']}")
    
    background_section = get_section(paper_id, "Introduction > Background")
    assert background_section is not None, "Failed to retrieve Background section"
    assert background_section["start_chunk_index"] == 1, "Background should start at chunk 1"
    print(f"✅ Background section: chunks {background_section['start_chunk_index']}-{background_section['end_chunk_index']}")
    
    methods_section = get_section(paper_id, "Methods")
    assert methods_section is not None, "Failed to retrieve Methods section"
    assert methods_section["start_chunk_index"] == 2, "Methods should start at chunk 2"
    print(f"✅ Methods section: chunks {methods_section['start_chunk_index']}-{methods_section['end_chunk_index']}")


def test_list_papers():
    """Test listing all papers."""
    print("\n=== Test 5: List Papers ===")
    
    papers = list_all_papers()
    assert len(papers) > 0, "Should have at least one paper"
    assert any(p["filename"] == "test_paper.pdf" for p in papers), "Should find test_paper.pdf"
    print(f"✅ Found {len(papers)} papers in database")
    for paper in papers:
        print(f"  - {paper['filename']}: {paper['num_chunks']} chunks")


def test_paper_structure(paper_id):
    """Test retrieving paper structure."""
    print("\n=== Test 6: Paper Structure ===")
    
    structure = get_paper_structure(paper_id)
    assert structure, "Failed to retrieve paper structure"
    assert structure["paper_id"] == paper_id, "Wrong paper_id in structure"
    assert "sections" in structure, "Structure should include sections"
    assert len(structure["sections"]) > 0, "Should have sections"
    
    print(f"✅ Paper structure retrieved:")
    print(f"  - Paper ID: {structure['paper_id']}")
    print(f"  - Filename: {structure['filename']}")
    print(f"  - Num chunks: {structure['num_chunks']}")
    print(f"  - Num sections: {len(structure['sections'])}")
    for section in structure["sections"]:
        print(f"    • {section['header_path']}: chunks {section['start_chunk_index']}-{section['end_chunk_index']}")


def test_real_pdf():
    """Test with a real PDF from the papers directory."""
    print("\n=== Test 7: Real PDF Integration ===")
    
    project_root = Path(__file__).parent.absolute()
    papers_dir = project_root / "papers"
    pdf_files = list(papers_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("⚠️  No PDF files found in ./papers/ directory, skipping real PDF test")
        return
    
    # Use the first PDF
    test_pdf = pdf_files[0]
    print(f"Testing with: {test_pdf.name}")
    
    # Extract and chunk
    doc = fitz.open(test_pdf)
    num_pages = len(doc)
    segments = extract_text_with_headers(doc)
    chunks = chunk_by_headers(segments)
    doc.close()
    
    print(f"  - Extracted {len(segments)} segments")
    print(f"  - Created {len(chunks)} chunks")
    
    # Insert into database
    paper_id = insert_paper(
        url=f"file://{test_pdf.absolute()}",
        filename=test_pdf.name,
        title=test_pdf.stem,
        num_pages=num_pages,
        chunking_method="header"
    )
    
    assert paper_id is not None, "Failed to insert real PDF"
    print(f"  - Inserted paper with ID: {paper_id}")
    
    # Insert chunks
    result = insert_chunks(paper_id, chunks)
    assert result, "Failed to insert chunks for real PDF"
    print(f"  - Inserted {len(chunks)} chunks")
    
    # Insert sections
    result = insert_sections(paper_id, chunks)
    assert result, "Failed to insert sections for real PDF"
    print(f"  - Created sections")
    
    # Verify structure
    structure = get_paper_structure(paper_id)
    assert structure, "Failed to retrieve structure for real PDF"
    print(f"✅ Real PDF indexed successfully:")
    print(f"  - {len(structure['sections'])} sections")
    print(f"  - {structure['num_chunks']} chunks")


def run_all_tests():
    """Run all integration tests."""
    print("=" * 60)
    print("Phase 3 Integration Tests: Database Indexing & Navigation")
    print("=" * 60)
    
    try:
        test_database_initialization()
        paper_id = test_paper_insertion()
        chunks = test_chunk_insertion(paper_id)
        test_section_insertion(paper_id, chunks)
        test_list_papers()
        test_paper_structure(paper_id)
        test_real_pdf()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

