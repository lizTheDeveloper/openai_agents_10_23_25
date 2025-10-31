"""
Embeddings module for generating text embeddings using MLX.

This module provides functionality to generate embeddings for text chunks
using Apple Silicon-optimized MLX models, and manage FAISS vector indices.
"""

from embeddings.generator import EmbeddingGenerator, get_embedding_generator
from embeddings.faiss_index import FAISSIndexManager

__all__ = [
    "EmbeddingGenerator",
    "get_embedding_generator",
    "FAISSIndexManager"
]

