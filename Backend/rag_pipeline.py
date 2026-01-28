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
from datetime import datetime


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
        self.conversation_memory = []  # Store last 10 conversations
        self.main_categories = set()  # Will be populated dynamically
        self.accessory_keywords = ['display', 'screen', 'stand', 'cooler', 'pad', 'case', 'bag', 'charger', 'battery', 'keyboard', 'mouse', 'accessory', 'cable']
        
        logger.info(f"Initializing RAG pipeline with model: {model_name}")
        self.load_and_process_products()
    
    def load_and_process_products(self):
        """Load products from CSV and prepare for RAG search."""
        try:
            # Load products CSV
            self.products_df = pd.read_csv(self.csv_path)
            logger.info(f"Loaded {len(self.products_df)} products from {self.csv_path}")
            
            # Analyze categories dynamically
            self._analyze_categories()
            
            # Limit to first 2000 products to avoid memory issues (increased for better coverage)
            if len(self.products_df) > 2000:
                logger.info("Limiting to first 2000 products to avoid memory issues")
                self.products_df = self.products_df.head(2000)
            
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
    
    def _analyze_categories(self):
        """Analyze and categorize product categories dynamically."""
        try:
            categories = self.products_df['category'].value_counts()
            logger.info(f"Found {len(categories)} unique categories")
            
            # Identify main product categories (not accessories)
            for category, count in categories.items():
                if pd.isna(category):
                    continue
                category_lower = str(category).lower()
                
                # Skip accessory categories
                if any(keyword in category_lower for keyword in self.accessory_keywords):
                    continue
                    
                # Main product categories
                if any(main_cat in category_lower for main_cat in ['laptop', 'desktop', 'pc', 'computer', 'gaming', 'workstation']):
                    self.main_categories.add(category)
                    
            logger.info(f"Identified {len(self.main_categories)} main product categories")
            
        except Exception as e:
            logger.error(f"Error analyzing categories: {str(e)}")
    
    def add_to_memory(self, query: str, response: str):
        """Add conversation to memory (keep last 10)."""
        self.conversation_memory.append({
            'query': query,
            'response': response,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only last 10 conversations
        if len(self.conversation_memory) > 10:
            self.conversation_memory = self.conversation_memory[-10:]
    
    def get_conversation_context(self) -> str:
        """Get recent conversation context for better responses."""
        if not self.conversation_memory:
            return ""
            
        context = "Recent conversation context:\n"
        for i, conv in enumerate(self.conversation_memory[-3:], 1):  # Last 3 for context
            context += f"{i}. User: {conv['query']}\n   AI: {conv['response'][:100]}...\n"
        return context
    
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
        Advanced relevance check to filter out irrelevant products and prioritize main categories.
        """
        query_lower = query.lower()
        product_category = str(product.get('category', '')).lower()
        product_name = str(product.get('name', '')).lower()
        
        # Strong filter for laptop searches - exclude clear accessories
        if 'laptop' in query_lower:
            # Exclude obvious laptop accessories
            laptop_accessory_terms = [
                'desk', 'stand', 'cooling', 'cooler', 'pad', 'case', 'bag', 'sleeve', 
                'charger', 'battery', 'keyboard', 'mouse', 'screen', 'display',
                'adapter', 'cable', 'dock', 'hub', 'riser', 'tray', 'portable folding',
                'laptop desk', 'laptop stand', 'laptop cooler', 'folding'
            ]
            
            if any(term in product_name for term in laptop_accessory_terms):
                return False\n        \n        # Check if this is an accessory when user wants main product
        if any(main_term in query_lower for main_term in ['laptop', 'desktop', 'pc', 'computer']):
            # If user is looking for main product, deprioritize accessories
            if any(acc_keyword in product_name or acc_keyword in product_category 
                   for acc_keyword in self.accessory_keywords):
                return False
                
        # Prioritize products from main categories
        if product.get('category') in self.main_categories:
            return True
            
        # Extract key terms from query
        key_terms = self.extract_key_terms(query)
        
        if not key_terms:
            return True  # If no specific terms, accept the product
        
        # Check if product matches key terms
        product_text = ' '.join([
            product_name,
            product_category,
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
        Dynamically extract key terms that must be present in relevant products.
        """
        query_lower = query.lower()
        
        # Product type terms
        product_types = ['laptop', 'desktop', 'pc', 'computer', 'workstation', 'gaming']
        
        # Brand terms
        brand_terms = ['ryzen', 'intel', 'amd', 'nvidia', 'gtx', 'rtx', 'radeon', 'asus', 'hp', 'lenovo', 'dell']
        
        # Feature terms
        feature_terms = ['gaming', 'budget', 'professional', 'student', 'business']
        
        # Spec terms
        spec_terms = ['processor', 'graphics', 'memory', 'storage', 'ssd', 'hdd', 'ram']
        
        all_terms = product_types + brand_terms + feature_terms + spec_terms
        
        return [term for term in all_terms if term in query_lower]
    
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
            
            # Get more candidates for better filtering
            top_indices = np.argsort(similarities)[::-1][:top_k * 5]  # Get more candidates for filtering
            
            results = []
            main_category_results = []
            other_results = []
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
                        # Prioritize main category products
                        if product.get('category') in self.main_categories:
                            main_category_results.append(product)
                        else:
                            other_results.append(product)
            
            # Combine results prioritizing main categories
            results = main_category_results[:top_k] + other_results[:max(0, top_k - len(main_category_results))]
            
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
        Format product search results into a natural, conversational response.
        
        Args:
            products: List of product dictionaries
            max_products: Maximum number of products to include in response
            query: Original search query for context
            
        Returns:
            Formatted response string
        """
        if not products:
            # More helpful no-results response based on query
            budget = self.extract_budget_from_query(query) if query else float('inf')
            query_lower = query.lower() if query else ""
            
            if 'laptop' in query_lower:
                if budget != float('inf'):
                    if budget < 50000:
                        return f"I couldn't find any laptops under {budget:,.0f}৳ in our current inventory. Our budget laptops start from around 50,000৳. Would you like me to show you some options in a slightly higher budget range, or are you interested in desktop computers which might offer better value?"
                    else:
                        return f"I couldn't find any laptops under {budget:,.0f}৳ that match your specific requirements. Let me know if you'd like to see our available laptops in different price ranges or if you have other preferences."
                else:
                    return "I couldn't find laptops matching your exact requirements. Could you tell me more about what you're looking for? For example, your budget range, intended use like gaming or work, or any specific features?"
            
            return "I couldn't find products matching those exact requirements. Could you help me understand better what you're looking for? I can search by product type, brand, budget range, or specific features."
        
        # Limit the number of products in response
        products = products[:max_products]
        
        # Check if we have conversation context
        context = self.get_conversation_context()
        follow_up = "Would you like more details about any of these?"
        
        if context and len(self.conversation_memory) > 1:
            follow_up = "Which of these interests you most, or would you like me to search for something else?"
        
        if len(products) == 1:
            product = products[0]
            response = f"I found a great option for you: **{product.get('name', 'Unknown Product')}**"
            
            if product.get('price'):
                response += f" priced at {product['price']}"
            
            if product.get('key_features') and len(str(product.get('key_features', ''))) > 10:
                # Extract key points from features
                features = str(product['key_features'])[:150].replace('[\'', '').replace('\']', '').replace('\'', '')
                response += f". Key features include: {features}..."
            
            response += f" {follow_up}"
            
        else:
            response = f"I found {len(products)} great options for you:\n"
            
            for i, product in enumerate(products, 1):
                response += f"{i}. **{product.get('name', 'Unknown Product')}**"
                
                if product.get('price'):
                    response += f" - {product['price']}"
                
                if i < len(products):
                    response += "\n"
            
            response += f"\n\n{follow_up}"
        
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
    Search products and return a voice-friendly response with conversation memory.
    This function is called by the voice agent.
    """
    global rag_pipeline
    
    try:
        if rag_pipeline is None:
            rag_pipeline = initialize_rag_pipeline()
            
        if rag_pipeline is None:
            return "I'm having trouble accessing the product database right now. Please try asking about a specific product or category."
        
        # Get conversation context for better understanding
        context = rag_pipeline.get_conversation_context()
        
        # Extract intent from query with context
        intent = rag_pipeline.extract_search_intent(query)
        logger.info(f"Extracted intent: {intent}")
        if context:
            logger.info(f"Using conversation context: {context[:200]}...")
        
        # Search for products
        products = rag_pipeline.search_products(query, top_k=5, score_threshold=0.3)  # Lower threshold for better recall
        
        # Format response for voice delivery
        response = rag_pipeline.format_product_response(products, max_products=3, query=query)
        
        # Add to conversation memory
        rag_pipeline.add_to_memory(query, response)
        
        return response
        
    except Exception as e:
        logger.error(f"Error in voice agent product search: {str(e)}")
        return f"I'm having trouble searching for products right now. Let me help you with our main categories: We have laptops starting from 30,000৳, desktop computers for various budgets, and gaming systems with dedicated graphics cards. Could you tell me more specifically what you're looking for?"

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