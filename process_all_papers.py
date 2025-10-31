#!/usr/bin/env python3
"""Process all papers in the papers directory"""
import sys
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).parent))

from database.operations import get_paper_by_filename, list_all_papers
from semantic_chunked_pdf_rag import PAPERS_DIR
import fitz
from pdf_processing import extract_text_with_headers
from chunking import chunk_by_headers
from database.operations import insert_paper, insert_chunks, insert_sections
from embeddings import get_embedding_generator, FAISSIndexManager
from database.operations import update_chunks_embedding_indices, get_all_chunks_for_paper
from utils.logger import get_logger

logger = get_logger()

def process_paper(filename):
    """Index and generate embeddings for one paper"""
    try:
        # Check if already indexed
        paper = get_paper_by_filename(filename)
        if paper:
            # Check if embeddings exist
            chunks = get_all_chunks_for_paper(paper['paper_id'])
            if chunks and any(c.get('embedding_index') is not None for c in chunks):
                logger.info(f"✓ {filename} - already processed")
                return True, "already_done"
            else:
                logger.info(f"→ {filename} - has paper, generating embeddings...")
                return generate_embeddings_for_paper(filename, paper['paper_id'])
        
        # Index the paper
        filepath = PAPERS_DIR / filename
        logger.info(f"→ {filename} - indexing...")
        
        doc = fitz.open(filepath)
        num_pages = len(doc)
        segments = extract_text_with_headers(doc)
        chunks = chunk_by_headers(segments)
        doc.close()
        
        # Extract title
        title = None
        if chunks and chunks[0].get("header_path"):
            first_header = chunks[0]["header_path"].split(" > ")[0]
            title = first_header if first_header else None
        
        # Insert into database
        paper_id = insert_paper(
            url=f"file://{filepath.absolute()}",
            filename=filename,
            title=title,
            num_pages=num_pages,
            chunking_method="header"
        )
        
        if not paper_id:
            return False, "db_insert_failed"
        
        insert_chunks(paper_id, chunks)
        insert_sections(paper_id, chunks)
        
        logger.info(f"✓ {filename} - indexed ({len(chunks)} chunks)")
        
        # Generate embeddings
        return generate_embeddings_for_paper(filename, paper_id)
        
    except Exception as e:
        logger.error(f"✗ {filename} - error: {e}")
        return False, str(e)

def generate_embeddings_for_paper(filename, paper_id):
    """Generate embeddings for an indexed paper"""
    try:
        chunks = get_all_chunks_for_paper(paper_id)
        if not chunks:
            return False, "no_chunks"
        
        # Generate embeddings
        embedding_gen = get_embedding_generator()
        texts = [chunk["text"] for chunk in chunks]
        chunk_ids = [chunk["chunk_id"] for chunk in chunks]
        
        embeddings = embedding_gen.generate_embeddings(texts, batch_size=32)
        
        # Add to FAISS
        faiss_manager = FAISSIndexManager("research_papers", embeddings.shape[1])
        if not faiss_manager.load_index():
            faiss_manager.create_index()
        
        start_idx = faiss_manager.index.ntotal
        faiss_manager.add_embeddings(embeddings, chunk_ids)
        
        # Update database
        updates = [(chunk_ids[i], start_idx + i) for i in range(len(chunk_ids))]
        update_chunks_embedding_indices(updates)
        
        # Save index
        faiss_manager.save_index()
        
        logger.info(f"✓ {filename} - embeddings generated ({len(embeddings)})")
        return True, "success"
        
    except Exception as e:
        logger.error(f"✗ {filename} - embedding error: {e}")
        return False, str(e)

def main():
    start_time = time.time()
    
    # Get all PDFs
    all_pdfs = sorted([f.name for f in PAPERS_DIR.glob("*.pdf")])
    logger.info(f"Found {len(all_pdfs)} PDF files")
    
    # Process each
    success_count = 0
    skip_count = 0
    error_count = 0
    
    for i, pdf in enumerate(all_pdfs, 1):
        logger.info(f"\n[{i}/{len(all_pdfs)}] Processing {pdf}")
        success, status = process_paper(pdf)
        
        if success:
            if status == "already_done":
                skip_count += 1
            else:
                success_count += 1
        else:
            error_count += 1
        
        # Progress update every 10 papers
        if i % 10 == 0:
            elapsed = time.time() - start_time
            rate = i / elapsed * 60  # papers per minute
            remaining = (len(all_pdfs) - i) / rate if rate > 0 else 0
            logger.info(f"\nProgress: {i}/{len(all_pdfs)} ({i*100//len(all_pdfs)}%) - "
                       f"{rate:.1f} papers/min - Est. {remaining:.1f} min remaining")
    
    # Summary
    duration = time.time() - start_time
    logger.info(f"\n" + "="*80)
    logger.info(f"COMPLETE - Processed {len(all_pdfs)} papers in {duration/60:.1f} minutes")
    logger.info(f"  Success: {success_count}")
    logger.info(f"  Already done: {skip_count}")
    logger.info(f"  Errors: {error_count}")
    logger.info("="*80)

if __name__ == "__main__":
    main()
