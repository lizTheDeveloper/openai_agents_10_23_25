"""
Test script to verify the MLX to numpy conversion fix.

This script tests embedding generation without going through the MCP server,
allowing us to verify the fix works before restarting the server.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from embeddings.generator import get_embedding_generator
from utils.logger import get_logger

logger = get_logger()


def test_embedding_generation():
    """Test that embedding generation works without MLX->numpy conversion errors."""
    print("\n" + "="*80)
    print("Testing MLX to numpy conversion fix")
    print("="*80 + "\n")
    
    try:
        # Initialize embedding generator
        print("1. Initializing embedding generator...")
        model_name = "mlx-community/Qwen3-0.6B-4bit"
        embedding_gen = get_embedding_generator(model_name)
        print(f"   ✓ Model loaded successfully (dim={embedding_gen.get_embedding_dimension()})")
        
        # Test with single text
        print("\n2. Testing single text embedding...")
        test_texts = ["This is a test sentence for embedding generation."]
        embeddings = embedding_gen.generate_embeddings(test_texts, batch_size=1)
        print(f"   ✓ Generated embeddings shape: {embeddings.shape}")
        print(f"   ✓ Embeddings dtype: {embeddings.dtype}")
        print(f"   ✓ Embeddings are contiguous: {embeddings.flags['C_CONTIGUOUS']}")
        
        # Test with multiple texts
        print("\n3. Testing batch embedding generation...")
        test_texts = [
            "The Transformer architecture uses self-attention mechanisms.",
            "Natural language processing has made significant progress.",
            "Machine learning models require large amounts of training data.",
            "Deep learning is a subset of machine learning.",
            "Artificial intelligence is transforming many industries."
        ]
        embeddings = embedding_gen.generate_embeddings(test_texts, batch_size=2)
        print(f"   ✓ Generated embeddings shape: {embeddings.shape}")
        print(f"   ✓ Embeddings dtype: {embeddings.dtype}")
        print(f"   ✓ All embeddings have correct dimension: {all(e.shape[0] == embedding_gen.get_embedding_dimension() for e in embeddings)}")
        
        # Verify embeddings are valid
        print("\n4. Verifying embeddings are valid...")
        import numpy as np
        assert embeddings.dtype == np.float32, "Embeddings should be float32"
        assert not np.any(np.isnan(embeddings)), "Embeddings should not contain NaN"
        assert not np.any(np.isinf(embeddings)), "Embeddings should not contain Inf"
        print("   ✓ Embeddings are valid (no NaN/Inf, correct dtype)")
        
        print("\n" + "="*80)
        print("✓ ALL TESTS PASSED - MLX to numpy conversion is working correctly!")
        print("="*80 + "\n")
        
        return True
        
    except Exception as e:
        print("\n" + "="*80)
        print(f"✗ TEST FAILED: {str(e)}")
        print("="*80 + "\n")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_embedding_generation()
    sys.exit(0 if success else 1)

