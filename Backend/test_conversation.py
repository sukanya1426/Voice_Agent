"""
Test script for conversational follow-up queries with smart context handling
"""

from rag_pipeline import search_products_for_voice_agent, initialize_rag_pipeline
from loguru import logger

def test_conversation():
    """Test conversational follow-up queries to ensure proper context handling."""
    
    logger.info("=" * 70)
    logger.info("Testing Smart Conversational Follow-ups")
    logger.info("=" * 70)
    
    # Initialize pipeline
    logger.info("\nInitializing RAG pipeline...")
    initialize_rag_pipeline()
    
    # Test 1: Laptop search
    logger.info("\n" + "=" * 70)
    logger.info("Test 1: Initial laptop search (original results)")
    logger.info("=" * 70)
    result1 = search_products_for_voice_agent('show me laptop under 1 Lakh taka')
    print(f"\nResult 1:\n{result1}\n")
    
    # Test 2: Cheaper alternatives (should return cheaper LAPTOPS than original)
    logger.info("\n" + "=" * 70)
    logger.info("Test 2: Cheaper alternatives (cheaper than original ~70k range)")
    logger.info("=" * 70)
    result2 = search_products_for_voice_agent('show me some cheaper alternatives')
    print(f"\nResult 2:\n{result2}\n")
    
    # Test 3: More expensive (should return MORE EXPENSIVE than ORIGINAL, not the cheaper ones!)
    logger.info("\n" + "=" * 70)
    logger.info("Test 3: More expensive (should be MORE expensive than original ~70k range)")
    logger.info("Expected: Laptops around 90k-120k, NOT 60k range")
    logger.info("=" * 70)
    result3 = search_products_for_voice_agent('show me some more expensive options')
    print(f"\nResult 3:\n{result3}\n")
    
    # Test 4: Even more expensive (should now be based on result 3)
    logger.info("\n" + "=" * 70)
    logger.info("Test 4: Even more expensive (based on previous result)")
    logger.info("=" * 70)
    result4 = search_products_for_voice_agent('show me even more expensive')
    print(f"\nResult 4:\n{result4}\n")
    
    # Test 5: New topic - Keyboard (should clear original laptop context)
    logger.info("\n" + "=" * 70)
    logger.info("Test 5: New topic - Keyboard (should clear laptop context)")
    logger.info("=" * 70)
    result5 = search_products_for_voice_agent('show me keyboard under 2000 taka')
    print(f"\nResult 5:\n{result5}\n")
    
    # Test 6: More expensive keyboards (should be keyboards, not laptops!)
    logger.info("\n" + "=" * 70)
    logger.info("Test 6: More expensive keyboards (should remain in keyboard context)")
    logger.info("=" * 70)
    result6 = search_products_for_voice_agent('show me more expensive options')
    print(f"\nResult 6:\n{result6}\n")
    
    logger.info("=" * 70)
    logger.info("✅ All conversational tests completed!")
    logger.info("=" * 70)
    logger.info("\nKey Improvements:")
    logger.info("- 'More expensive' after 'cheaper' now references ORIGINAL search")
    logger.info("- Context switches when changing product types (laptop → keyboard)")
    logger.info("- Avoids showing same products multiple times")

if __name__ == "__main__":
    test_conversation()
