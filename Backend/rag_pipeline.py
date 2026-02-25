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
        self.model_name = model_name
        self.model = None  # Load only when needed
        self.products_df = None
        self.embeddings = None
        self.product_descriptions = []
        self.conversation_memory = []  # Store last 10 conversations
        self.last_search_results = []  # Store last search results for this session
        self.original_search_results = []  # Store original search before follow-ups
        self.main_categories = set()  # Will be populated dynamically
        self.accessory_keywords = ['display', 'screen', 'stand', 'cooler', 'pad', 'case', 'bag', 'charger', 'battery', 'keyboard', 'mouse', 'accessory', 'cable']
        self.major_brands = ['hp', 'asus', 'acer', 'lenovo', 'dell', 'apple', 'macbook', 'microsoft', 'msi', 'gigabyte', 'chuwi', 'walton', 'sony', 'samsung', 'toshiba', 'fujitsu', 'huawei', 'xiaomi', 'avita', 'razer', 'alienware', 'intel', 'amd', 'ryzen', 'nvidia', 'tecno', 'walton', 'casio', 'canon', 'nikon', 'sony']
        self.embeddings_cache_path = "embeddings_cache.npy"
        self.descriptions_cache_path = "descriptions_cache.json"
        
        logger.info(f"Initializing RAG pipeline with model: {model_name}")
        self.load_and_process_products()
    
    def save_session(self, session_id: str):
        """Save conversation memory and last results to disk for this session."""
        if not session_id:
            return
            
        try:
            os.makedirs("session_memory", exist_ok=True)
            file_path = os.path.join("session_memory", f"{session_id}.json")
            
            # Prepare data to save (don't save the full objects, just what's needed)
            state = {
                'conversation_memory': self.conversation_memory,
                'last_search_results': self.last_search_results,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(file_path, 'w') as f:
                json.dump(state, f)
            logger.info(f"💾 Saved session state for {session_id}")
        except Exception as e:
            logger.error(f"Error saving session state: {str(e)}")

    def load_session(self, session_id: str):
        """Load conversation memory and last results from disk for this session."""
        if not session_id:
            return
            
        try:
            file_path = os.path.join("session_memory", f"{session_id}.json")
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    state = json.load(f)
                    self.conversation_memory = state.get('conversation_memory', [])
                    self.last_search_results = state.get('last_search_results', [])
                logger.info(f"📂 Loaded session state for {session_id}")
            else:
                logger.info(f"🆕 No existing session state for {session_id}")
        except Exception as e:
            logger.error(f"Error loading session state: {str(e)}")
    
    def load_and_process_products(self):
        """Load products from CSV and prepare for RAG search with caching."""
        try:
            # Load products CSV
            self.products_df = pd.read_csv(self.csv_path)
            logger.info(f"Loaded {len(self.products_df)} products from {self.csv_path}")
            
            # Analyze categories dynamically
            self._analyze_categories()
            
            # Load all products - 10k rows is well within memory limits
            logger.info(f"Using all {len(self.products_df)} products for maximum coverage")
            
            # Try to load cached embeddings
            if os.path.exists(self.embeddings_cache_path) and os.path.exists(self.descriptions_cache_path):
                try:
                    logger.info("Loading cached embeddings...")
                    self.embeddings = np.load(self.embeddings_cache_path)
                    with open(self.descriptions_cache_path, 'r') as f:
                        self.product_descriptions = json.load(f)
                    logger.info("Successfully loaded cached embeddings and descriptions")
                    return
                except Exception as e:
                    logger.warning(f"Failed to load cache, regenerating: {str(e)}")
            
            # Create comprehensive product descriptions for better search
            self.product_descriptions = []
            
            for idx, row in self.products_df.iterrows():
                description_parts = []
                
                # Add product name and extract brand if missing
                product_name = str(row.get('name', ''))
                if pd.notna(row.get('name')):
                    description_parts.append(f"Product: {product_name}")
                
                # Dynamic brand extraction - modify the dataframe directly
                if pd.isna(row.get('brand')) or str(row.get('brand')).lower() == 'nan':
                    for brand in self.major_brands:
                        if brand in product_name.lower():
                            self.products_df.at[idx, 'brand'] = brand.capitalize()
                            row['brand'] = brand.capitalize() # Also update local dict for current loop
                            break
                
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
            
            # Generate embeddings only if not cached
            logger.info("Generating embeddings for product descriptions (this may take a minute)...")
            
            # Load model temporarily
            self.model = SentenceTransformer(self.model_name)
            
            batch_size = 200  # Increased batch size for faster processing
            all_embeddings = []
            
            for i in range(0, len(self.product_descriptions), batch_size):
                batch = self.product_descriptions[i:i + batch_size]
                batch_embeddings = self.model.encode(batch, show_progress_bar=False)
                all_embeddings.append(batch_embeddings)
                logger.info(f"Processed batch {i//batch_size + 1}/{(len(self.product_descriptions)-1)//batch_size + 1}")
            
            self.embeddings = np.vstack(all_embeddings)
            
            # Save embeddings to cache
            logger.info("Saving embeddings to cache...")
            np.save(self.embeddings_cache_path, self.embeddings)
            with open(self.descriptions_cache_path, 'w') as f:
                json.dump(self.product_descriptions, f)
            logger.info("Embeddings cached successfully")
            
            # Unload model to free memory
            del self.model
            self.model = None
            import gc
            gc.collect()
            logger.info("Model unloaded from memory to reduce resource usage")
            
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
                elif any(comp_cat in category_lower for comp_cat in ['ram', 'ssd', 'hdd', 'processor', 'graphics card', 'motherboard']):
                    # Add component categories to a separate set if needed for future logic
                    pass
                    
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
        Relevance check to filter out irrelevant products (less aggressive than before).
        """
        query_lower = query.lower()
        product_category = str(product.get('category', '')).lower()
        product_name = str(product.get('name', '')).lower()
        
        # Moderate brand filtering - only if specific brand mentioned
        query_brands = [brand for brand in self.major_brands if f" {brand} " in f" {query_lower} " or query_lower.startswith(brand) or query_lower.endswith(brand)]
        if query_brands:
            # If a brand is specifically mentioned, prefer products with that brand
            if not any(brand in product_name or brand in product_category for brand in query_brands):
                # Don't completely exclude, just mark as less relevant
                if product.get('similarity_score', 0) < 0.5:
                    return False
                
        # More lenient filter for laptop searches
        if 'laptop' in query_lower:
            # Only exclude obvious non-laptop items
            strict_exclude_terms = [
                'ram ', 'memory ', ' ssd', ' hdd', 'graphics card', 'gpu ', 
                'processor ', 'motherboard', 'casing', 'power supply ',
                'cooling pad', 'laptop stand', 'laptop bag', 'laptop case',
                'charger', 'adapter', 'cable', 'dock', 'hub', 'portable folding'
            ]
            
            # Check if product is clearly an accessory/component
            for term in strict_exclude_terms:
                if term in product_name and 'laptop' not in product_name:
                    return False
        
        # Filter for keyboard searches
        if 'keyboard' in query_lower and 'laptop' not in query_lower:
            # If searching for keyboards specifically, permit replacements but maybe downrank slightly later
            # For now, allow them but strictly exclude actual LAPTOPS matching "keyboard" description
            if 'laptop' in product_name and 'keyboard' not in product_name:
                return False

                        
        
        # Out of stock filtering - only exclude if clearly out of stock and low relevance
        availability = str(product.get('availability', '')).lower()
        if 'out of stock' in availability or 'upcoming' in availability:
            if product.get('similarity_score', 0) < 0.6:
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
        # Handle both "lakh" and "Lakh" with optional "taka"
        lakh_patterns = [
            r'under\s+([0-9.]+)\s*(?:lakh|Lakh)',
            r'below\s+([0-9.]+)\s*(?:lakh|Lakh)',
            r'less\s+than\s+([0-9.]+)\s*(?:lakh|Lakh)',
            r'maximum\s+([0-9.]+)\s*(?:lakh|Lakh)',
            r'max\s+([0-9.]+)\s*(?:lakh|Lakh)',
            r'budget\s+of\s+([0-9.]+)\s*(?:lakh|Lakh)',
            r'up\s+to\s+([0-9.]+)\s*(?:lakh|Lakh)',
            r'within\s+([0-9.]+)\s*(?:lakh|Lakh)',
            r'([0-9.]+)\s*(?:lakh|Lakh)\s*(?:taka|৳)?'
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
    
    def search_products(self, query: str, top_k: int = 5, score_threshold: float = 0.25) -> List[Dict[str, Any]]:
        """
        Search for products based on natural language query with improved precision and price filtering.
        
        Args:
            query: Natural language search query
            top_k: Number of top results to return
            score_threshold: Minimum similarity score threshold (reduced for better recall)
            
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
            
            # Load model temporarily if not loaded
            if self.model is None:
                logger.info("Loading model for query encoding...")
                self.model = SentenceTransformer(self.model_name)
            
            # Generate embedding for the processed query
            query_embedding = self.model.encode([processed_query], show_progress_bar=False)
            
            # Compute cosine similarity
            similarities = cosine_similarity(query_embedding, self.embeddings)[0]
            
            # Unload model after use to save memory
            del self.model
            self.model = None
            import gc
            gc.collect()
            
            # Apply keyword boosting for exact matches
            similarities = self.apply_keyword_boosting(query.lower(), similarities)
            
            # Get more candidates for better filtering
            top_indices = np.argsort(similarities)[::-1][:100]  # Get 100 candidates for filtering
            
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
                        # Determine if this product belongs to the "target category" based on query
                        is_target_cat = False
                        
                        # Check dynamic intent from query
                        query_intent = self.extract_search_intent(query)
                        target_cat = query_intent.get('category')
                        
                        if target_cat:
                            # If query has specific category intent, prioritize that
                            prod_cat = str(product.get('category', '')).lower()
                            prod_name = str(product.get('name', '')).lower()
                            
                            if target_cat in prod_cat or target_cat in prod_name:
                                is_target_cat = True
                        else:
                            # Fallback to general "main categories" list
                            if product.get('category') in self.main_categories:
                                is_target_cat = True
                                
                        if is_target_cat:
                            main_category_results.append(product)
                        else:
                            other_results.append(product)
            
            # Combine results prioritizing target/main categories
            # If looking for specific accessory (keyboard), allow ONLY that category if possible
            if self.extract_search_intent(query).get('category') in ['keyboard', 'mouse', 'monitor']:
                 results = main_category_results[:top_k]
                 # If not enough, fill with other results (but be careful)
                 if len(results) < top_k:
                     results += other_results[:max(0, top_k - len(results))]
            else:
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
            'graphics': ['graphics', 'gpu', 'video card', 'rtx', 'gtx'],
            'keyboard': ['keyboard', 'keypad'],
            'mouse': ['mouse', 'mice'],
            'monitor': ['monitor', 'display', 'screen'],
            'accessory': ['bag', 'case', 'adapter', 'cable', 'stand', 'cooler']
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
    
    def simplify_product_name(self, name: str) -> str:
        """
        Simplify product name by removing common specifications to keep it concise for voice.
        """
        if not name or pd.isna(name):
            return "Unknown Product"
            
        # Common spec patterns to remove
        patterns = [
            r'\b\d+GB\b', r'\b\d+TB\b', r'\b\d+MB\b', # Memory/Storage
            r'\bRAM\b', r'\bSSD\b', r'\bHDD\b', r'\bNVMe\b', # Component types
            r'\bCore i\d\b', r'\bRyzen \d\b', r'\bIntel\b', r'\bAMD\b', # CPUs
            r'\bi[3579]-\d+[\w]*\b', r'\br[3579]-\d+[\w]*\b', # CPU Models like i5-1335U
            r'\b\d+(?:th|rd|nd|st) Gen\b', # Generation
            r'\b\d+(?:\.\d+)?(?:GHz|MHz)\b', # Clock speed
            r'\b\d+(?:\.\d+)?\s*(?:to|@)\s*\d+(?:\.\d+)?\s*(?:GHz|MHz)\b', # Clock speed ranges
            r'\b\d+px\b', r'\b\d+Hz\b', # Screen specs
            r'\b\d+-inch\b', r'\b\d+"\b', # Screen size
            r'\bFHD\b', r'\bUHD\b', r'\bWUXGA\b', r'\bOLED\b', r'\bIPS\b', # Display
            r'\bWindows \d+\b', r'\bWin \d+\b', # OS
            r'\b(?!Laptop|PC|Desktop)\b[\w\d]+TU\b', # Model suffixes (specific to HP/ASUS often)
            r'\(.*?\)', # Remove anything in parentheses
        ]
        
        simplified = name
        for pattern in patterns:
            simplified = re.sub(pattern, '', simplified, flags=re.IGNORECASE)
            
        # Remove trailing/leading punctuation and extra commas
        simplified = simplified.replace(',', ' ')
        
        # Clean up extra whitespace
        simplified = re.sub(r'\s+', ' ', simplified).strip()
        
        # Final cleanup for common trailing words that look like leftover specs
        simplified = re.sub(r'\s+[\w\d]*\d[\w\d]*$', '', simplified) # Remove trailing models
        simplified = simplified.strip('. ').strip() # Remove trailing dots and spaces
        
        # If we stripped too much, return the original first 4 words
        if len(simplified.split()) < 2:
            return ' '.join(name.split()[:4])

            
        return simplified


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
            
            logger.warning(f"No products found for query: '{query}', budget: {budget}")
            
            if 'laptop' in query_lower:
                if budget != float('inf'):
                    if budget < 50000:
                        return f"I couldn't find any laptops under {budget:,.0f}৳ in our current inventory. Our entry-level laptops start from around 50,000৳. Would you like me to show you some budget-friendly options, or would you prefer to look at desktop computers which offer better value?"
                    elif budget < 100000:
                        return f"I'm searching for laptops under {budget:,.0f}৳... Let me show you our available options in that range. We have several good laptops between 50,000৳ and {budget:,.0f}৳."
                    else:
                        return f"I couldn't find exact matches for laptops under {budget:,.0f}৳. However, we have many excellent options. Would you like to see our popular laptops in the 80,000-150,000৳ range?"
                else:
                    return "I couldn't find laptops matching your exact requirements. Could you tell me more about what you're looking for? For example, your budget range, intended use like gaming or work, or any specific features?"
            elif 'desktop' in query_lower or 'pc' in query_lower:
                if budget != float('inf'):
                    return f"I didn't find desktop PCs matching your exact criteria under {budget:,.0f}৳. Our desktop PCs start from 22,000৳. Would you like to see some options?"
                else:
                    return "I couldn't find desktop PCs matching those requirements. Could you specify your budget range or what you'll use it for?"
            elif 'keyboard' in query_lower or 'mouse' in query_lower:
                    return "I couldn't find those specific accessories. Please note we primarily stock laptop replacement parts and complete computer systems. Would you like to check our desktop computers which include these?"
            
            return "I couldn't find products matching those exact requirements. Could you help me understand better what you're looking for? I can search by product type (laptop/desktop), brand, budget range, or specific features."

        
        # Limit the number of products in response
        products = products[:max_products]
        
        # Check if we have conversation context
        context = self.get_conversation_context()
        follow_up = "Would you like more details about any of these?"
        
        if context and len(self.conversation_memory) > 1:
            follow_up = "Which of these interests you most, or would you like me to search for something else?"
        
        if len(products) == 1:
            product = products[0]
            name = self.simplify_product_name(product.get('name', 'Unknown Product'))
            response = f"I've found an excellent option that fits your needs perfectly: the **{name}**."
            
            if product.get('price'):
                response += f" It's currently priced at {product['price']}."
            
            response += f" {follow_up}"
            
        else:
            # Check if searching for keyboards but only finding replacements
            is_keyboard_search = 'keyboard' in query.lower()
            if is_keyboard_search:
                 has_replacements = any('for' in p.get('name', '').lower() for p in products)
                 if has_replacements:
                     response = f"I found {len(products)} keyboard options, mostly replacement parts for laptops:\n"
                 else:
                     response = f"I've found {len(products)} fantastic options for you that I think you'll really like:\n"
            else:
                 response = f"I've found {len(products)} fantastic options for you that I think you'll really like:\n"
            
            for i, product in enumerate(products, 1):
                name = self.simplify_product_name(product.get('name', 'Unknown Product'))
                price = product.get('price', 'Call for price')
                response += f"{i}. The **{name}** at {price}."
                
                if i < len(products):
                    response += "\n"
            
            response += f"\n\n{follow_up}"



        
        return response

    def format_single_product_details(self, product: Dict[str, Any]) -> str:
        """Format detailed information for a single product with icons and sections."""
        name = product.get('name', 'Product Details')
        response = f"Here are the details for **{name}**:\n\n"
        
        if product.get('price'):
            response += f"**Price**: {product['price']}\n"
            
        if product.get('availability'):
            response += f"**Availability**: {product['availability']}\n"
            
        brand = product.get('brand')
        if not brand or str(brand).lower() == 'nan':
            # Fallback brand extraction
            product_name_lower = name.lower()
            for b in self.major_brands:
                if b in product_name_lower:
                    brand = b.capitalize()
                    break
        
        if brand and str(brand).lower() != 'nan':
            response += f"**Brand**: {brand}\n"
            
        if product.get('key_features') and str(product.get('key_features')) != 'nan':
            features = str(product['key_features']).replace('[\'', '').replace('\']', '').replace('\'', '')
            response += f"\n**Key Features**:\n{features}\n"
            
        if product.get('specifications') and str(product.get('specifications')) != 'nan':
            specs = str(product['specifications'])
            if len(specs) > 20:
                response += f"\n**Specifications**: {specs[:300]}...\n"
                
        if product.get('warranty_info') and str(product.get('warranty_info')) != 'nan':
            response += f"**Warranty**: {product['warranty_info']}\n"
            
        response += "\nWould you like me to help you with anything else regarding this product?"
        return response
    
    def get_product_type(self, product_name: str, category: str) -> str:
        """
        Extract the main product type from name and category.
        Returns: 'laptop', 'desktop', 'keyboard', 'mouse', 'monitor', 'accessory', 'component', 'other'
        """
        text = f"{product_name} {category}".lower()
        
        # Check for main product types in order of specificity
        if any(term in text for term in ['laptop', 'notebook', 'ultrabook', 'chromebook', 'macbook']):
            # Exclude laptop accessories
            if any(term in text for term in ['laptop bag', 'laptop case', 'laptop stand', 'laptop desk', 'laptop cooler', 'laptop pad', 'laptop keyboard']):
                return 'accessory'
            # Laptop replacement keyboards are accessories, not laptops
            if 'keyboard for' in text or 'replacement keyboard' in text:
                return 'accessory'
            return 'laptop'
        elif any(term in text for term in ['desktop pc', 'desktop computer', 'tower pc', 'gaming pc', 'workstation pc']):
            return 'desktop'
        elif 'keyboard' in text:
            # Distinguish between standalone keyboards and laptop replacement keyboards
            if any(term in text for term in ['for laptop', 'replacement', 'for acer', 'for hp', 'for dell', 'for asus', 'for lenovo']):
                return 'accessory'
            # Standalone keyboards
            return 'keyboard'
        elif 'mouse' in text:
            return 'mouse'
        elif 'monitor' in text or 'display' in text:
            return 'monitor'
        elif any(term in text for term in ['processor', 'cpu', 'ram', 'memory', 'ssd', 'hdd', 'graphics card', 'gpu', 'motherboard']):
            return 'component'
        elif any(term in text for term in ['bag', 'case', 'stand', 'desk', 'cooler', 'pad', 'cable', 'adapter']):
            return 'accessory'
        else:
            return 'other'
    
    def handle_follow_up_query(self, query: str, last_products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Handle follow-up queries like 'show me cheaper options', 'more expensive', 'similar products'.
        
        Args:
            query: The follow-up query
            last_products: List of products from the previous search
            
        Returns:
            List of products matching the follow-up criteria
        """
        query_lower = query.lower()
        
        if not last_products:
            logger.warning("No previous search results to base follow-up query on")
            return []
        
        # Determine if we should use original or last search as reference
        # If user asks for "more expensive" after "cheaper", use original reference
        reference_products = last_products
        use_original = False
        
        if (any(word in query_lower for word in ['expensive', 'more expensive', 'premium', 'higher', 'better']) and 
            self.original_search_results and 
            len(self.conversation_memory) >= 2):
            # Check if the last query was about cheaper options
            last_query = self.conversation_memory[-1].get('query', '').lower() if self.conversation_memory else ''
            if any(word in last_query for word in ['cheaper', 'less expensive', 'lower price', 'budget']):
                # User asked for cheaper, now wants more expensive - use original reference
                reference_products = self.original_search_results
                use_original = True
                logger.info("Using original search results as reference (user wants more expensive after cheaper)")
        
        # Get reference product (first from reference)
        reference_product = reference_products[0]
        reference_price = self.parse_price_from_string(reference_product.get('price', ''))
        reference_category = reference_product.get('category', '')
        reference_name = reference_product.get('name', '')
        reference_type = self.get_product_type(reference_name, reference_category)
        
        logger.info(f"Follow-up query based on: {reference_name} ({reference_price}৳, type: {reference_type}, using_original: {use_original})")
        
        # Determine follow-up intent
        if any(word in query_lower for word in ['cheaper', 'less expensive', 'lower price', 'budget']):
            logger.info("Looking for cheaper alternatives")
            intent = 'cheaper'
        elif any(word in query_lower for word in ['expensive', 'more expensive', 'premium', 'higher', 'better']):
            logger.info("Looking for more expensive alternatives")
            intent = 'expensive'
        elif any(word in query_lower for word in ['similar', 'like this', 'same', 'alternative']):
            logger.info("Looking for similar products")
            intent = 'similar'
        else:
            logger.warning(f"Could not determine follow-up intent from: {query}")
            return []
        
        # Find matching products
        matching_products = []
        for _, row in self.products_df.iterrows():
            product = row.to_dict()
            product_name = str(product.get('name', ''))
            product_category = str(product.get('category', ''))
            product_price = self.parse_price_from_string(product.get('price', ''))
            
            # Skip if same product
            if product_name == reference_name:
                continue
            
            # Skip if invalid price
            if product_price == float('inf') or product_price <= 0:
                continue
            
            # Check if same product type
            product_type = self.get_product_type(product_name, product_category)
            if product_type != reference_type:
                continue
            
            # Skip products we've already shown
            already_shown = any(prod.get('name') == product_name for prod in last_products)
            if already_shown and not use_original:
                continue
            
            # Apply price filter based on intent
            if intent == 'cheaper':
                if product_price >= reference_price:
                    continue
                # Prefer products around 60-80% of reference price
                ideal_price = reference_price * 0.7
                price_diff = abs(product_price - ideal_price) / reference_price
                product['similarity_score'] = 1.0 - min(price_diff, 1.0)
                
            elif intent == 'expensive':
                if product_price <= reference_price:
                    continue
                # Prefer products around 120-150% of reference price
                ideal_price = reference_price * 1.3
                price_diff = abs(product_price - ideal_price) / max(reference_price, 1)
                product['similarity_score'] = 1.0 - min(price_diff * 0.5, 1.0)  # Less penalty for expensive
                
            elif intent == 'similar':
                # Within ±30% of reference price
                if product_price < reference_price * 0.7 or product_price > reference_price * 1.3:
                    continue
                price_diff = abs(product_price - reference_price) / reference_price
                product['similarity_score'] = 1.0 - price_diff
            
            matching_products.append(product)
        
        if not matching_products:
            logger.warning(f"No {reference_type}s found matching {intent} criteria")
            return []
        
        # Sort by similarity score and return top results
        results = sorted(matching_products, key=lambda x: x.get('similarity_score', 0), reverse=True)[:10]
        logger.info(f"Found {len(results)} {reference_type}s matching {intent} query")
        return results


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
            rag_pipeline.products_df['name'].str.contains(product_name, case=False, na=False, regex=False)
        ]
        
        if matching_products.empty:
            # Try a broader match if exact match fails
            name_query = " ".join(product_name.split()[:3])
            matching_products = rag_pipeline.products_df[
                rag_pipeline.products_df['name'].str.contains(name_query, case=False, na=False, regex=False)
            ]
            
        if matching_products.empty:
            return f"I couldn't find detailed information for '{product_name}'. Could you please specify a different product?"
        
        product = matching_products.iloc[0].to_dict()
        return rag_pipeline.format_single_product_details(product)
        
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
                self.products_df['name'].str.contains(product_name, case=False, na=False, regex=False)
            ]
            
            if matching_products.empty:
                return f"I couldn't find detailed information for '{product_name}'. Could you please specify the exact product name?"
            
            product = matching_products.iloc[0].to_dict()
            
            response = f"Here are the detailed specifications for {product.get('name', 'the product')}:\n\n"
            
            if product.get('price'):
                response += f"Price: {product['price']}\n"
            
            if product.get('category'):
                response += f"Category: {product['category']}\n"
            
            if product.get('specifications'):
                specs = str(product['specifications'])
                if specs != 'nan':
                    response += f"Specifications: {specs}\n"
            
            if product.get('key_features'):
                features = str(product['key_features'])
                if features != 'nan':
                    response += f"Key Features: {features}\n"
            
            if product.get('brand'):
                response += f"Brand: {product['brand']}\n"
            
            if product.get('availability'):
                response += f"Availability: {product['availability']}\n"
            
            if product.get('warranty_info'):
                response += f"Warranty: {product['warranty_info']}\n"
            
            if product.get('url'):
                response += f"More info: {product['url']}\n"
            
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
        try:
            rag_pipeline = ProductRAGPipeline(csv_path)
            logger.info("RAG pipeline initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize RAG pipeline: {str(e)}")
            rag_pipeline = None
    return rag_pipeline

def search_products_for_voice_agent(query: str, session_id: str = None) -> str:
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
        
        # Load session state if session_id is provided
        if session_id:
            rag_pipeline.load_session(session_id)
            
        # Get conversation context for better understanding
        context = rag_pipeline.get_conversation_context()
        query_lower = query.lower()
        
        logger.info(f"Processing query: '{query}'")
        
        # Robust follow-up detection
        is_follow_up = any(word in query_lower for word in ['cheaper', 'expensive', 'similar', 'alternative', 'less', 'more', 'like this', 'same', 'other option'])
        is_details_request = any(word in query_lower for word in ['info', 'detail', 'spec', 'about', 'tell me', 'tell more', 'first', 'second', 'third'])
        
        # Detect if this is a completely new search topic (different product type)
        if rag_pipeline.last_search_results and not is_follow_up:
            # Get the product type from last search
            last_product = rag_pipeline.last_search_results[0]
            last_type = rag_pipeline.get_product_type(
                str(last_product.get('name', '')),
                str(last_product.get('category', ''))
            )
            
            # Try to detect product type in current query
            query_types = []
            if 'laptop' in query_lower:
                query_types.append('laptop')
            if 'desktop' in query_lower or 'pc' in query_lower:
                query_types.append('desktop')
            if 'keyboard' in query_lower:
                query_types.append('keyboard')
            if 'mouse' in query_lower:
                query_types.append('mouse')
            if 'monitor' in query_lower:
                query_types.append('monitor')
            
            # If query mentions a different product type, clear original results
            if query_types and last_type not in query_types:
                logger.info(f"New search topic detected (was: {last_type}, now: {query_types}), clearing original results")
                rag_pipeline.original_search_results = []
        
        # Handle request for details about a previous product
        if is_details_request and rag_pipeline.last_search_results:
            # Detect index in list
            idx = -1
            if any(w in query_lower for w in ['first', ' 1st', 'number one', 'option one']): idx = 0
            elif any(w in query_lower for w in ['second', ' 2nd', 'number two', 'option two']): idx = 1
            elif any(w in query_lower for w in ['third', ' 3rd', 'number three', 'option three']): idx = 2
            
            if idx != -1 and idx < len(rag_pipeline.last_search_results):
                target_product = rag_pipeline.last_search_results[idx]
                return rag_pipeline.format_single_product_details(target_product)
            
            # Match by brand/name mentioned in query from last results
            for product in rag_pipeline.last_search_results:
                name_parts = product['name'].lower().split()
                if any(part in query_lower for part in name_parts if len(part) > 3):
                    return rag_pipeline.format_single_product_details(product)
        
        # Handle follow-up query (cheaper/expensive/similar)
        if is_follow_up and rag_pipeline.last_search_results:
            logger.info("Detected follow-up query, using last search results as context")
            products = rag_pipeline.handle_follow_up_query(query, rag_pipeline.last_search_results)
            
            # If handle_follow_up_query found nothing, don't fallback to general search immediately
            # Try once with broader category search or just tell the user
            if not products:
                logger.info("Follow-up search returned no results, trying broader search")
                # Fallback to general search but stay in same category
                products = rag_pipeline.search_products(f"{rag_pipeline.last_search_results[0].get('category', '').split('>')[-1]} {query}", top_k=5)
        else:
            # This is a NEW search (not a follow-up), so store as original
            intent = rag_pipeline.extract_search_intent(query)
            logger.info(f"Extracted intent: {intent}")
            products = rag_pipeline.search_products(query, top_k=10, score_threshold=0.2)
            logger.info(f"Search returned {len(products)} products")
            
            # Store as original search results for smarter follow-ups
            if products:
                rag_pipeline.original_search_results = products[:5]
                logger.info(f"Stored original search results for smart follow-ups")
        
        # Store results for potential follow-up queries
        if products:
            rag_pipeline.last_search_results = products[:5]
            logger.info(f"Stored {len(rag_pipeline.last_search_results)} products for follow-up")
        else:
            logger.warning(f"No products found for query: '{query}'")
        
        # Format response for voice delivery
        response = rag_pipeline.format_product_response(products, max_products=3, query=query)
        
        # Add to conversation memory
        rag_pipeline.add_to_memory(query, response)
        
        # Save session state if session_id is provided
        if session_id:
            # Only save if we have meaningful results or memory
            if products or rag_pipeline.conversation_memory:
                rag_pipeline.save_session(session_id)
            
        return response
        
    except Exception as e:
        logger.error(f"Error in voice agent product search: {str(e)}", exc_info=True)
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
            return "I'm having trouble accessing our product gallery right now. What else can I help you with?"
            
        # Find product by name (case insensitive partial match)
        # First try exact model match from last search if possible
        for p in (rag_pipeline.last_search_results or []):
            if product_name.lower() in p.get('name', '').lower():
                return rag_pipeline.format_single_product_details(p)

        matching_products = rag_pipeline.products_df[
            rag_pipeline.products_df['name'].str.contains(product_name, case=False, na=False)
        ]
        
        if matching_products.empty:
            return f"I couldn't find the specific details for '{product_name}' in our current inventory. Could you tell me a bit more about what you're looking for? I might have a better alternative!"
        
        product = matching_products.iloc[0].to_dict()
        return rag_pipeline.format_single_product_details(product)
        
    except Exception as e:
        logger.error(f"Error getting product details for voice agent: {str(e)}")
        return "I'm having a little trouble pulling up those specs. Could you try asking about a different model?"