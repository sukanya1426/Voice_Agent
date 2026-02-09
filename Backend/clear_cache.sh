#!/bin/bash

# Script to clear RAG pipeline cache
# Use this if you need to regenerate embeddings after updating the product database

echo "Clearing RAG pipeline cache..."

# Remove cache files
if [ -f "embeddings_cache.npy" ]; then
    rm embeddings_cache.npy
    echo "✓ Removed embeddings_cache.npy"
fi

if [ -f "descriptions_cache.json" ]; then
    rm descriptions_cache.json
    echo "✓ Removed descriptions_cache.json"
fi

# Remove Python cache
if [ -d "__pycache__" ]; then
    rm -rf __pycache__
    echo "✓ Removed __pycache__"
fi

echo ""
echo "Cache cleared successfully!"
echo "The embeddings will be regenerated on the next run."
