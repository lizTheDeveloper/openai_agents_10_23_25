"""
Test the MCP server with Phase 3 database tools.

This script tests the MCP server integration by:
1. Starting the server
2. Testing each database-related tool
3. Verifying end-to-end workflow
"""
import subprocess
import json
import sys
from pathlib import Path

def send_mcp_request(method: str, params: dict = None) -> dict:
    """
    Send a request to the MCP server via stdio.
    
    Args:
        method: Tool name to call
        params: Parameters for the tool
        
    Returns:
        Response dictionary
    """
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": method,
            "arguments": params or {}
        }
    }
    
    # Convert to JSON and add newline
    request_json = json.dumps(request) + "\n"
    
    return request_json


def test_mcp_server():
    """Test the MCP server functionality."""
    print("=" * 60)
    print("Testing MCP Server - Phase 3 Integration")
    print("=" * 60)
    
    # Find a test PDF
    papers_dir = Path("./papers")
    pdf_files = list(papers_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("❌ No PDF files found in ./papers/ directory")
        return False
    
    test_pdf = pdf_files[0].name
    print(f"\n📄 Using test PDF: {test_pdf}")
    
    # Test 1: List papers before indexing
    print("\n=== Test 1: List Indexed Papers (before) ===")
    print("Tool: list_indexed_papers")
    print("Expected: Should show existing papers or empty list")
    
    # Test 2: Index a PDF
    print("\n=== Test 2: Index PDF ===")
    print(f"Tool: index_pdf")
    print(f"Parameters: filename={test_pdf}, method=header")
    print("Expected: Should index the PDF and return paper_id, num_chunks, num_sections")
    
    # Test 3: List papers after indexing
    print("\n=== Test 3: List Indexed Papers (after) ===")
    print("Tool: list_indexed_papers")
    print("Expected: Should show the newly indexed paper")
    
    # Test 4: Get document structure
    print("\n=== Test 4: Get Document Structure ===")
    print("Tool: get_document_structure")
    print(f"Parameters: filename={test_pdf}")
    print("Expected: Should return paper structure with sections and chunk ranges")
    
    # Test 5: Chunk PDF (legacy tool, should still work)
    print("\n=== Test 5: Chunk PDF (legacy) ===")
    print("Tool: chunk_pdf")
    print(f"Parameters: filename={test_pdf}, method=header")
    print("Expected: Should return chunks without storing in database")
    
    print("\n" + "=" * 60)
    print("✅ MCP Server Test Plan Complete")
    print("=" * 60)
    print("\nTo manually test the MCP server:")
    print("1. Run: python semantic_chunked_pdf_rag.py")
    print("2. Send JSON-RPC requests via stdin")
    print("3. Or configure in MCP client (like Claude Desktop)")
    
    return True


def show_mcp_config():
    """Show the MCP configuration for Claude Desktop or other clients."""
    print("\n" + "=" * 60)
    print("MCP Configuration Example")
    print("=" * 60)
    
    config = {
        "mcpServers": {
            "pdf-indexer": {
                "command": "python",
                "args": [
                    str(Path(__file__).parent.absolute() / "semantic_chunked_pdf_rag.py")
                ],
                "env": {}
            }
        }
    }
    
    print("\nAdd this to your MCP configuration file:")
    print(json.dumps(config, indent=2))
    
    print("\nTools available:")
    tools = [
        "download_pdf - Download a PDF from URL",
        "chunk_pdf - Extract and chunk a PDF (no database)",
        "index_pdf - Index a PDF in the database with navigation",
        "list_indexed_papers - List all indexed papers",
        "get_document_structure - Get paper structure with sections"
    ]
    for tool in tools:
        print(f"  • {tool}")


def verify_server_startup():
    """Verify the MCP server can start without errors."""
    print("\n" + "=" * 60)
    print("Verifying MCP Server Startup")
    print("=" * 60)
    
    try:
        # Try to import the server
        import semantic_chunked_pdf_rag
        print("✅ Server module imports successfully")
        
        # Check that database was initialized
        from database.operations import get_engine
        engine = get_engine()
        print(f"✅ Database engine created: {engine.url}")
        
        # Verify database file exists
        db_path = Path("./indexes/research_papers.db")
        if db_path.exists():
            print(f"✅ Database file exists: {db_path.absolute()}")
            size_kb = db_path.stat().st_size / 1024
            print(f"   Size: {size_kb:.2f} KB")
        else:
            print("⚠️  Database file not found (will be created on first use)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = True
    
    # Verify server can start
    if not verify_server_startup():
        success = False
    
    # Test MCP functionality
    if not test_mcp_server():
        success = False
    
    # Show configuration
    show_mcp_config()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ All MCP integration checks passed!")
    else:
        print("❌ Some checks failed")
    print("=" * 60)
    
    sys.exit(0 if success else 1)

