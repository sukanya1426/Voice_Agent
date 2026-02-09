"""
Test script for RAG pipeline to verify search functionality and performance.
Run this to check if the search is working correctly after optimization.
"""

from rag_pipeline import search_products_for_voice_agent, initialize_rag_pipeline
from loguru import logger
import time

def test_search_queries():
    """Test various search queries to ensure the system is working."""
    
    logger.info("=" * 60)
    logger.info("Starting RAG Pipeline Test")
    logger.info("=" * 60)
    
    # Initialize pipeline
    logger.info("\n1. Initializing RAG pipeline...")
    start_time = time.time()
    initialize_rag_pipeline()
    init_time = time.time() - start_time
    logger.info(f"✓ Pipeline initialized in {init_time:.2f} seconds")
    
    # Test queries
    test_queries = [
        "show me laptop under 1 Lakh taka",
        "gaming laptop under 100000",
        "budget desktop pc",
        "AMD Ryzen desktop",
        "laptop for students under 60000"
    ]
    
    logger.info("\n2. Testing search queries...")
    logger.info("-" * 60)
    
    for i, query in enumerate(test_queries, 1):
        logger.info(f"\nTest {i}: '{query}'")
        logger.info("-" * 40)
        
        start_time = time.time()
        result = search_products_for_voice_agent(query)
        search_time = time.time() - start_time
        
        logger.info(f"Search completed in {search_time:.2f} seconds")
        logger.info(f"Response:\n{result}\n")
    
    logger.info("=" * 60)
    logger.info("Test completed successfully!")
    logger.info("=" * 60)

if __name__ == "__main__":
    test_search_queries()
