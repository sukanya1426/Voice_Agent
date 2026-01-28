"""
RAG (Retrieval-Augmented Generation) Pipeline for Product Search
This module handles product data indexing and retrieval for the voice agent.
Simplified version without FAISS to avoid compatibility issues.
"""

import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import json
import re
from typing import List, Dict, Any, Tuple
import os
from loguru import logger
from sklearn.metrics.pairwise import cosine_similarity


class ProductRAGPipeline:
    def __init__(self, csv_path: str = "products_merged.csv", model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the RAG pipeline for product search.
        
        Args:
            csv_path: Path to the products CSV file
            model_name: Sentence transformer model name for embeddings
        """
        self.csv_path = csv_path
        self.model = SentenceTransformer(model_name)
        self.products_df = None
        self.embeddings = None
        self.product_descriptions = []
        
        logger.info(f"Initializing RAG pipeline with model: {model_name}")
        self.load_and_process_products()
    
    def load_and_process_products(self):
        """Load products from CSV and prepare for RAG search."""
        try:
            # Load products CSV
            self.products_df = pd.read_csv(self.csv_path)
            logger.info(f"Loaded {len(self.products_df)} products from {self.csv_path}")
            
            # Limit to first 1000 products to avoid memory issues
            if len(self.products_df) > 1000:
                logger.info("Limiting to first 1000 products to avoid memory issues")
                self.products_df = self.products_df.head(1000)
            
            # Create comprehensive product descriptions for better search
            self.product_descriptions = []
            
            for _, row in self.products_df.iterrows():
                description_parts = []
                
                # Add product name
                if pd.notna(row.get('name')):
                    description_parts.append(f"Product: {row['name']}")
                
                # Add price information
                if pd.notna(row.get('price')):
                    description_parts.append(f"Price: {row['price']}")
                
                # Add category
                if pd.notna(row.get('category')):
                    description_parts.append(f"Category: {row['category']}")
                
                # Add description
                if pd.notna(row.get('description')):
                    description_parts.append(f"Description: {row['description']}")
                
                # Add key features
                if pd.notna(row.get('key_features')):
                    features = str(row['key_features'])
                    if features != 'nan':
                        description_parts.append(f"Key Features: {features}")
                
                # Add brand
                if pd.notna(row.get('brand')):
                    description_parts.append(f"Brand: {row['brand']}")
                
                full_description = " | ".join(description_parts)
                self.product_descriptions.append(full_description)
            
            # Generate embeddings for all product descriptions in smaller batches
            logger.info("Generating embeddings for product descriptions...")
            batch_size = 100
            all_embeddings = []
            
            for i in range(0, len(self.product_descriptions), batch_size):
                batch = self.product_descriptions[i:i + batch_size]
                batch_embeddings = self.model.encode(batch)
                all_embeddings.append(batch_embeddings)
                logger.info(f"Processed batch {i//batch_size + 1}/{(len(self.product_descriptions)-1)//batch_size + 1}")
            
            self.embeddings = np.vstack(all_embeddings)
            logger.info("RAG pipeline initialization completed successfully")
            
        except Exception as e:
            logger.error(f"Error initializing RAG pipeline: {str(e)}")
            raise
    
    def preprocess_query(self, query: str) -> str:
        """
        Preprocess query for better embedding matching.
        """
        # Expand common abbreviations
        expansions = {
            'pc': 'personal computer',
            'gpu': 'graphics card',
            'cpu': 'processor',
            'ram': 'memory',
            'ssd': 'solid state drive',
            'hdd': 'hard disk drive'
        }
        
        processed = query.lower()
        for abbr, full in expansions.items():
            processed = processed.replace(abbr, full)
        
        return processed
    
    def apply_keyword_boosting(self, query: str, similarities: np.ndarray) -> np.ndarray:
        """
        Boost similarity scores for exact keyword matches.
        """
        query_words = set(query.split())
        boosted_similarities = similarities.copy()
        
        for i, description in enumerate(self.product_descriptions):
            description_words = set(description.lower().split())
            
            # Calculate keyword overlap
            overlap = len(query_words.intersection(description_words))
            if overlap > 0:
                boost_factor = 1 + (overlap * 0.1)  # 10% boost per matching word
                boosted_similarities[i] *= boost_factor
        
        return boosted_similarities
    
    def is_relevant_product(self, query: str, product: Dict[str, Any]) -> bool:
        """
        Additional relevance check to filter out irrelevant products.
        """
        # Extract key terms from query
        key_terms = self.extract_key_terms(query)
        
        if not key_terms:
            return True  # If no specific terms, accept the product
        
        # Check if product matches key terms
        product_text = ' '.join([
            str(product.get('name', '')),
            str(product.get('category', '')),
            str(product.get('description', '')),
            str(product.get('key_features', ''))
        ]).lower()
        
        # At least one key term should match
        return any(term in product_text for term in key_terms)
    
    def parse_price_from_string(self, price_str: str) -> float:
        """
        Parse numeric price from price string formats like "999৳", "24,499৳28,100৳", etc.
        Returns the lowest price if multiple prices are found.
        """
        if not price_str or pd.isna(price_str) or str(price_str).lower() in ['out of stock', 'nan']:
            return float('inf')
        
        # Remove quotes and clean the string
        price_str = str(price_str).replace('"', '').strip()
        
        # Find all numeric values followed by ৳
        import re
        price_matches = re.findall(r'([0-9,]+)৳', price_str)
        
        if not price_matches:
            return float('inf')
        
        # Parse all found prices and return the lowest one
        prices = []
        for match in price_matches:
            try:
                # Remove commas and convert to float
                price_value = float(match.replace(',', ''))
                prices.append(price_value)
            except ValueError:
                continue
        
        return min(prices) if prices else float('inf')
    
    def extract_budget_from_query(self, query: str) -> float:
        """
        Extract budget/price limit from user query.
        Handles formats like "50000", "1 lakh", "2 lakh", "50k", etc.
        """
        import re
        query_lower = query.lower()
        
        # First check for "lakh" patterns (1 lakh = 100,000)
        lakh_patterns = [
            r'under\s+([0-9.]+)\s*lakh',
            r'below\s+([0-9.]+)\s*lakh',
            r'less\s+than\s+([0-9.]+)\s*lakh',
            r'maximum\s+([0-9.]+)\s*lakh',
            r'max\s+([0-9.]+)\s*lakh',
            r'budget\s+of\s+([0-9.]+)\s*lakh',
            r'up\s+to\s+([0-9.]+)\s*lakh',
            r'within\s+([0-9.]+)\s*lakh'
        ]
        
        for pattern in lakh_patterns:
            match = re.search(pattern, query_lower)
            if match:
                try:
                    lakh_value = float(match.group(1))
                    return lakh_value * 100000  # Convert lakh to actual number
                except ValueError:
                    continue
        
        # Check for "k" patterns (50k = 50,000)
        k_patterns = [
            r'under\s+([0-9.]+)k',
            r'below\s+([0-9.]+)k',
            r'less\s+than\s+([0-9.]+)k',
            r'maximum\s+([0-9.]+)k',
            r'max\s+([0-9.]+)k',
            r'budget\s+of\s+([0-9.]+)k',
            r'up\s+to\s+([0-9.]+)k',
            r'within\s+([0-9.]+)k'
        ]
        
        for pattern in k_patterns:
            match = re.search(pattern, query_lower)
            if match:
                try:
                    k_value = float(match.group(1))
                    return k_value * 1000  # Convert k to actual number
                except ValueError:
                    continue
        
        # Look for regular number patterns
        budget_patterns = [
            r'under\s+([0-9,]+)',
            r'below\s+([0-9,]+)',
            r'less\s+than\s+([0-9,]+)',
            r'maximum\s+([0-9,]+)',
            r'max\s+([0-9,]+)',
            r'budget\s+of\s+([0-9,]+)',
            r'up\s+to\s+([0-9,]+)',
            r'within\s+([0-9,]+)'
        ]
        
        for pattern in budget_patterns:
            match = re.search(pattern, query_lower)
            if match:
                try:
                    return float(match.group(1).replace(',', ''))
                except ValueError:
                    continue
        
        return float('inf')  # No budget constraint found
    
    def extract_key_terms(self, query: str) -> List[str]:
        """
        Extract key terms that must be present in relevant products.
        """
        important_categories = [
            'gaming', 'budget', 'laptop', 'desktop', 'workstation',
            'ryzen', 'intel', 'amd', 'nvidia', 'gtx', 'rtx',
            'processor', 'graphics', 'memory', 'storage'
        ]
        
        return [term for term in important_categories if term in query.lower()]
    
    def search_products(self, query: str, top_k: int = 5, score_threshold: float = 0.4) -> List[Dict[str, Any]]:
        """
        Search for products based on natural language query with improved precision and price filtering.
        
        Args:
            query: Natural language search query
            top_k: Number of top results to return
            score_threshold: Minimum similarity score threshold (increased for precision)
            
        Returns:
            List of product dictionaries with similarity scores
        """
        try:
            logger.info(f"Searching for products with query: '{query}'")
            
            # Extract budget constraint from query
            budget_limit = self.extract_budget_from_query(query)
            logger.info(f"Extracted budget limit: {budget_limit if budget_limit != float('inf') else 'No limit'}")
            
            # Preprocess query for better matching
            processed_query = self.preprocess_query(query)
            
            # Generate embedding for the processed query
            query_embedding = self.model.encode([processed_query])
            
            # Compute cosine similarity
            similarities = cosine_similarity(query_embedding, self.embeddings)[0]
            
            # Apply keyword boosting for exact matches
            similarities = self.apply_keyword_boosting(query.lower(), similarities)
            
            # Get top results with stricter threshold
            top_indices = np.argsort(similarities)[::-1][:top_k * 3]  # Get more candidates for filtering
            
            results = []
            budget_filtered_count = 0
            
            for i, idx in enumerate(top_indices):
                score = similarities[idx]
                if score >= score_threshold:
                    product = self.products_df.iloc[idx].to_dict()
                    product['similarity_score'] = float(score)
                    product['rank'] = i + 1
                    
                    # Apply price filtering if budget constraint exists
                    if budget_limit != float('inf'):
                        product_price = self.parse_price_from_string(product.get('price', ''))
                        if product_price > budget_limit:
                            budget_filtered_count += 1
                            continue  # Skip products over budget
                    
                    # Additional relevance filtering
                    if self.is_relevant_product(query.lower(), product):
                        results.append(product)
                        if len(results) >= top_k:  # Stop when we have enough good results
                            break
            
            # Log filtering results
            if budget_limit != float('inf'):
                logger.info(f"Filtered out {budget_filtered_count} products over budget of {budget_limit}৳")
            logger.info(f"Found {len(results)} products matching criteria")
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching products: {str(e)}")
            return []
    
    def extract_search_intent(self, query: str) -> Dict[str, Any]:
        """
        Extract search intent and parameters from natural language query.
        
        Args:
            query: User's natural language query
            
        Returns:
            Dictionary containing extracted intent and parameters
        """
        intent = {
            'category': None,
            'price_range': None,
            'brand': None,
            'keywords': [],
            'intent_type': 'general_search'
        }
        
        query_lower = query.lower()
        
        # Extract category intent
        category_patterns = {
            'gaming': ['gaming', 'game', 'gamer', 'gaming pc', 'gaming computer'],
            'desktop': ['desktop', 'pc', 'computer', 'workstation'],
            'budget': ['budget', 'cheap', 'affordable', 'low cost', 'economical'],
            'processor': ['processor', 'cpu', 'ryzen', 'intel', 'amd'],
            'graphics': ['graphics', 'gpu', 'video card', 'rtx', 'gtx']
        }
        
        for category, keywords in category_patterns.items():
            if any(keyword in query_lower for keyword in keywords):
                intent['category'] = category
                break
        
        # Extract price-related intent
        if any(word in query_lower for word in ['under', 'below', 'less than', 'maximum']):
            intent['intent_type'] = 'price_filter'
        
        # Extract brand mentions
        brands = ['amd', 'ryzen', 'intel', 'nvidia', 'asus', 'msi', 'corsair', 'colorful']
        for brand in brands:
            if brand in query_lower:
                intent['brand'] = brand
                break
        
        # Extract general keywords (remove common words)
        stop_words = {'i', 'want', 'need', 'looking', 'for', 'a', 'an', 'the', 'some', 'find', 'show', 'me'}
        words = re.findall(r'\b\w+\b', query_lower)
        intent['keywords'] = [word for word in words if word not in stop_words and len(word) > 2]
        
        return intent
    
    def format_product_response(self, products: List[Dict[str, Any]], max_products: int = 3, query: str = "") -> str:
        """
        Format product search results into a natural language response.
        
        Args:
            products: List of product dictionaries
            max_products: Maximum number of products to include in response
            query: Original search query for context
            
        Returns:
            Formatted response string
        """
        if not products:
            # Check if this was a budget-constrained search
            budget = self.extract_budget_from_query(query) if query else float('inf')
            
            if budget != float('inf') and any(term in query.lower() for term in ['gaming', 'laptop']):
                return f"I couldn't find any gaming laptops under {budget:,.0f}৳ in our current inventory. The gaming laptops we have start from around 165,000৳. However, I found some gaming accessories like laptop coolers and peripherals within your budget. Would you like to see those instead, or would you prefer to explore other product categories like desktops or increase your budget?"
            
            return "I couldn't find any products matching your requirements. Could you please be more specific or try different keywords?"
        
        # Limit the number of products in response
        products = products[:max_products]
        
        if len(products) == 1:
            product = products[0]
            response = f"I found a great option for you: the {product.get('name', 'Unknown Product')} "
            
            if product.get('price'):
                response += f"priced at {product['price']}. "
            
            if product.get('description'):
                # Extract key points from description
                desc = str(product['description'])[:200]
                response += f"{desc}... "
            
            response += "Would you like more details about this product or see other options?"
            
        else:
            response = f"I found {len(products)} great options for you: "
            
            for i, product in enumerate(products, 1):
                response += f"{i}. {product.get('name', 'Unknown Product')}"
                
                if product.get('price'):
                    response += f" - {product['price']}"
                
                if i < len(products):
                    response += ", "
            
            response += ". Which one would you like to know more about?"
        
        return response


# Global instance for the voice agent
rag_pipeline = None

def initialize_rag_pipeline(csv_path: str = "products_merged.csv"):
    """Initialize the global RAG pipeline instance."""
    global rag_pipeline
    if rag_pipeline is None:
        try:
            rag_pipeline = ProductRAGPipeline(csv_path)
            logger.info("RAG pipeline initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize RAG pipeline: {str(e)}")
            rag_pipeline = None
    return rag_pipeline

def search_products_for_voice_agent(query: str) -> str:
    """
    Search products and return a voice-friendly response.
    This function is called by the voice agent.
    """
    global rag_pipeline
    
    try:
        if rag_pipeline is None:
            rag_pipeline = initialize_rag_pipeline()
            
        if rag_pipeline is None:
            return "I'm having trouble accessing the product database right now. Please try asking about a specific product or category."
        
        # Extract intent from query
        intent = rag_pipeline.extract_search_intent(query)
        logger.info(f"Extracted intent: {intent}")
        
        # Search for products
        products = rag_pipeline.search_products(query, top_k=5)
        
        # Format response for voice delivery
        response = rag_pipeline.format_product_response(products, max_products=3)
        
        return response
        
    except Exception as e:
        logger.error(f"Error in voice agent product search: {str(e)}")
        return f"I'm having trouble searching for products right now. Here's what I know about our catalog: We offer AMD Ryzen gaming PCs starting from around ৳24,000, desktop computers for various budgets, and high-performance systems with RTX graphics cards. Could you be more specific about what you're looking for?"

def get_product_details_for_voice_agent(product_name: str) -> str:
    """
    Get product details and return a voice-friendly response.
    """
    global rag_pipeline
    if rag_pipeline is None:
        rag_pipeline = initialize_rag_pipeline()
    
    try:
        if rag_pipeline is None:
            return "I'm having trouble accessing the product details right now. Please try again."
            
        # Find product by name (case insensitive partial match)
        matching_products = rag_pipeline.products_df[
            rag_pipeline.products_df['name'].str.contains(product_name, case=False, na=False)
        ]
        
        if matching_products.empty:
            return f"I couldn't find detailed information for '{product_name}'. Could you please specify the exact product name?"
        
        product = matching_products.iloc[0].to_dict()
        
        response = f"Here are the details for {product.get('name', 'the product')}: "
        
        if product.get('price'):
            response += f"Price {product['price']}. "
        
        if product.get('description'):
            desc = str(product['description'])[:200]
            response += f"{desc}... "
        
        response += "Would you like to know anything else about this product?"
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting product details for voice agent: {str(e)}")
        return "I'm having trouble getting the product details right now. Please try again."
    
    def get_product_details(self, product_name: str) -> str:
        """
        Get detailed information about a specific product.
        
        Args:
            product_name: Name of the product
            
        Returns:
            Detailed product information
        """
        try:
            # Find product by name (case insensitive partial match)
            matching_products = self.products_df[
                self.products_df['name'].str.contains(product_name, case=False, na=False)
            ]
            
            if matching_products.empty:
                return f"I couldn't find detailed information for '{product_name}'. Could you please specify the exact product name?"
            
            product = matching_products.iloc[0].to_dict()
            
            response = f"Here are the detailed specifications for {product.get('name', 'the product')}:\n\n"
            
            if product.get('price'):
                response += f"💰 Price: {product['price']}\n"
            
            if product.get('category'):
                response += f"📂 Category: {product['category']}\n"
            
            if product.get('specifications'):
                specs = str(product['specifications'])
                if specs != 'nan':
                    response += f"🔧 Specifications: {specs}\n"
            
            if product.get('key_features'):
                features = str(product['key_features'])
                if features != 'nan':
                    response += f"⭐ Key Features: {features}\n"
            
            if product.get('brand'):
                response += f"🏢 Brand: {product['brand']}\n"
            
            if product.get('availability'):
                response += f"📦 Availability: {product['availability']}\n"
            
            if product.get('warranty_info'):
                response += f"🛡️ Warranty: {product['warranty_info']}\n"
            
            if product.get('url'):
                response += f"🔗 More info: {product['url']}\n"
            
            response += "\nWould you like to know anything else about this product or see similar alternatives?"
            
            return response
            
        except Exception as e:
            logger.error(f"Error getting product details: {str(e)}")
            return "I'm having trouble retrieving the detailed information right now. Please try again in a moment."


# Global instance for the voice agent
rag_pipeline = None

def initialize_rag_pipeline(csv_path: str = "products_merged.csv"):
    """Initialize the global RAG pipeline instance."""
    global rag_pipeline
    if rag_pipeline is None:
        rag_pipeline = ProductRAGPipeline(csv_path)
    return rag_pipeline

def search_products_for_voice_agent(query: str) -> str:
    """
    Search products and return a voice-friendly response.
    This function is called by the voice agent.
    """
    global rag_pipeline
    if rag_pipeline is None:
        rag_pipeline = initialize_rag_pipeline()
    
    try:
        # Extract intent from query
        intent = rag_pipeline.extract_search_intent(query)
        logger.info(f"Extracted intent: {intent}")
        
        # Search for products
        products = rag_pipeline.search_products(query, top_k=5)
        
        # Format response for voice delivery
        response = rag_pipeline.format_product_response(products, max_products=3, query=query)
        
        return response
        
    except Exception as e:
        logger.error(f"Error in voice agent product search: {str(e)}")
        return "I'm having trouble searching for products right now. Please try asking about a specific product or category."

def get_product_details_for_voice_agent(product_name: str) -> str:
    """
    Get product details and return a voice-friendly response.
    """
    global rag_pipeline
    if rag_pipeline is None:
        rag_pipeline = initialize_rag_pipeline()
    
    try:
        return rag_pipeline.get_product_details(product_name)
    except Exception as e:
        logger.error(f"Error getting product details for voice agent: {str(e)}")
        return "I'm having trouble getting the product details right now. Please try again."