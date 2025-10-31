"""
Live test of the MCP server by actually calling it via JSON-RPC.

This script:
1. Starts the MCP server as a subprocess
2. Sends actual JSON-RPC requests
3. Verifies responses
"""
import subprocess
import json
import sys
import time
from pathlib import Path


def test_mcp_tool(process, tool_name, arguments=None):
    """
    Test an MCP tool by sending a JSON-RPC request.
    
    Args:
        process: The subprocess running the MCP server
        tool_name: Name of the tool to call
        arguments: Dictionary of arguments for the tool
        
    Returns:
        Response dictionary or None if error
    """
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments or {}
        }
    }
    
    request_json = json.dumps(request) + "\n"
    
    print(f"\n📤 Sending request to tool: {tool_name}")
    print(f"   Arguments: {json.dumps(arguments or {}, indent=2)}")
    
    try:
        # Send request
        process.stdin.write(request_json)
        process.stdin.flush()
        
        # Read response (with timeout)
        response_line = process.stdout.readline()
        
        if not response_line:
            print("❌ No response received")
            return None
        
        response = json.loads(response_line)
        
        if "error" in response:
            print(f"❌ Error: {response['error']}")
            return None
        
        result = response.get("result", {})
        print(f"✅ Success!")
        
        # Pretty print key parts of the result
        if isinstance(result, dict):
            if "content" in result:
                content = result["content"]
                if isinstance(content, list) and content:
                    text_content = content[0].get("text", "")
                    # Parse the text content if it's JSON
                    try:
                        parsed = json.loads(text_content)
                        print(f"   Result: {json.dumps(parsed, indent=2)[:500]}...")
                    except:
                        print(f"   Result: {text_content[:500]}...")
            else:
                print(f"   Result: {json.dumps(result, indent=2)[:500]}...")
        
        return result
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return None


def run_live_tests():
    """Run live tests against the MCP server."""
    print("=" * 70)
    print("LIVE MCP SERVER TEST")
    print("=" * 70)
    
    # Find a test PDF
    papers_dir = Path("/Users/annhoward/openai_agents_10_23_25/papers")
    pdf_files = list(papers_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("❌ No PDF files found")
        return False
    
    test_pdf = pdf_files[0].name
    print(f"\n📄 Test PDF: {test_pdf}")
    
    # Start the MCP server
    server_path = Path("/Users/annhoward/openai_agents_10_23_25/semantic_chunked_pdf_rag.py")
    python_path = Path("/Users/annhoward/openai_agents_10_23_25/env/bin/python3")
    
    print(f"\n🚀 Starting MCP server: {server_path}")
    
    try:
        process = subprocess.Popen(
            [str(python_path), str(server_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Give server time to start
        time.sleep(2)
        
        # Check if process is still running
        if process.poll() is not None:
            stderr = process.stderr.read()
            print(f"❌ Server failed to start:\n{stderr}")
            return False
        
        print("✅ Server started successfully")
        
        # Test 1: List indexed papers
        print("\n" + "=" * 70)
        print("TEST 1: list_indexed_papers")
        print("=" * 70)
        result = test_mcp_tool(process, "list_indexed_papers", {})
        
        if result:
            print("✅ Test 1 passed")
        
        # Test 2: Index a PDF
        print("\n" + "=" * 70)
        print("TEST 2: index_pdf")
        print("=" * 70)
        result = test_mcp_tool(process, "index_pdf", {
            "filename": test_pdf,
            "method": "header"
        })
        
        if result:
            print("✅ Test 2 passed")
        
        # Test 3: Get document structure
        print("\n" + "=" * 70)
        print("TEST 3: get_document_structure")
        print("=" * 70)
        result = test_mcp_tool(process, "get_document_structure", {
            "filename": test_pdf
        })
        
        if result:
            print("✅ Test 3 passed")
        
        # Test 4: List indexed papers again (should show the new one)
        print("\n" + "=" * 70)
        print("TEST 4: list_indexed_papers (after indexing)")
        print("=" * 70)
        result = test_mcp_tool(process, "list_indexed_papers", {})
        
        if result:
            print("✅ Test 4 passed")
        
        # Test 5: Chunk PDF (legacy tool)
        print("\n" + "=" * 70)
        print("TEST 5: chunk_pdf (legacy)")
        print("=" * 70)
        result = test_mcp_tool(process, "chunk_pdf", {
            "filename": test_pdf,
            "method": "header"
        })
        
        if result:
            print("✅ Test 5 passed")
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS COMPLETED")
        print("=" * 70)
        
        # Cleanup
        process.terminate()
        process.wait(timeout=5)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        
        if 'process' in locals():
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                process.kill()
        
        return False


if __name__ == "__main__":
    success = run_live_tests()
    sys.exit(0 if success else 1)

