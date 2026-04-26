"""
Embedding Service for Phase 2
Handles text embedding generation using Google Gemini API or OpenAI text-embedding-3-small
"""

import logging
import asyncio
from typing import List, Dict, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Try to import Google Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logging.warning("Google Gemini library not available")

# Try to import OpenAI
try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI library not available, using mock embeddings")

# Try to import sentence-transformers as fallback
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logging.warning("sentence-transformers not available")

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingResult:
    """Result of embedding generation"""
    text: str
    embedding: List[float]
    embedding_id: str
    model_used: str
    processing_time: float
    token_count: int
    success: bool
    error_message: Optional[str] = None


class EmbeddingService:
    """Service for generating text embeddings"""
    
    def __init__(self, config: dict):
        self.config = config.get('embeddings', {})
        self.use_api = self.config.get('use_api', False)  # Free-only: default to false
        self.api_provider = self.config.get('api_provider', 'none')
        self.model_name = self.config.get('model', 'all-MiniLM-L6-v2')
        self.batch_size = self.config.get('batch_size', 100)
        self.max_tokens = self.config.get('max_tokens', 8192)
        self.dimension = self.config.get('dimension', 384)  # sentence-transformers default
        self.cache_enabled = self.config.get('cache_enabled', True)
        self.fallback_enabled = self.config.get('fallback_enabled', True)
        
        # API keys (only used if use_api is true)
        self.gemini_api_key = self.config.get('gemini_api_key')
        self.openai_api_key = self.config.get('openai_api_key')
        
        # Initialize clients
        self.gemini_client = None
        self.openai_client = None
        self.fallback_model = None
        
        # Free-only mode: prioritize sentence-transformers (local, no API costs)
        if not self.use_api or self.api_provider == 'none':
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                try:
                    self.fallback_model = SentenceTransformer(self.model_name)
                    self.dimension = self.fallback_model.get_sentence_embedding_dimension()
                    logger.info(f"Using free sentence-transformers model: {self.model_name} (dim={self.dimension})")
                except Exception as e:
                    logger.error(f"Failed to initialize sentence-transformers: {e}")
            else:
                logger.warning("sentence-transformers not available, will use mock embeddings")
        else:
            # Paid API mode (only if explicitly enabled)
            if self.api_provider == 'gemini' and GEMINI_AVAILABLE and self.gemini_api_key:
                try:
                    genai.configure(api_key=self.gemini_api_key)
                    self.gemini_client = genai
                    self.model_name = 'models/text-embedding-004'
                    self.dimension = 768
                    logger.info(f"Google Gemini client initialized with model: {self.model_name}")
                except Exception as e:
                    logger.error(f"Failed to initialize Gemini client: {e}")
            
            elif self.api_provider == 'openai' and OPENAI_AVAILABLE and self.openai_api_key:
                try:
                    self.openai_client = OpenAI(api_key=self.openai_api_key)
                    self.model_name = self.config.get('model', 'text-embedding-3-small')
                    self.dimension = self.config.get('dimension', 1536)
                    logger.info(f"OpenAI client initialized with model: {self.model_name}")
                except Exception as e:
                    logger.error(f"Failed to initialize OpenAI client: {e}")
            
            # Fallback to sentence-transformers if API fails
            if not self.gemini_client and not self.openai_client and SENTENCE_TRANSFORMERS_AVAILABLE and self.fallback_enabled:
                try:
                    self.fallback_model = SentenceTransformer('all-MiniLM-L6-v2')
                    self.dimension = self.fallback_model.get_sentence_embedding_dimension()
                    logger.info(f"Using sentence-transformers fallback model with dimension: {self.dimension}")
                except Exception as e:
                    logger.error(f"Failed to initialize fallback model: {e}")
        
        # Embedding cache
        self.embedding_cache = {} if self.cache_enabled else None
        
        # Performance tracking
        self.total_embeddings = 0
        self.total_processing_time = 0.0
        self.cache_hits = 0
        
        logger.info(f"EmbeddingService initialized - Model: {self.model_name}, Dimension: {self.dimension}")
    
    def generate_embedding_gemini(self, text: str) -> tuple[List[float], float]:
        """Generate embedding using Google Gemini API"""
        if not self.gemini_client:
            raise ValueError("Gemini client not initialized")
        
        start_time = time.time()
        
        try:
            model = self.gemini_client.GenerativeModel(self.model_name)
            result = model.embed_content(text)
            embedding = result.embedding
            processing_time = time.time() - start_time
            
            return embedding, processing_time
            
        except Exception as e:
            logger.error(f"Gemini embedding generation failed: {e}")
            raise
    
    def generate_embedding_openai(self, text: str) -> tuple[List[float], float]:
        """Generate embedding using OpenAI API"""
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized")
        
        start_time = time.time()
        
        try:
            response = self.openai_client.embeddings.create(
                model=self.model_name,
                input=text,
                encoding_format="float"
            )
            
            embedding = response.data[0].embedding
            processing_time = time.time() - start_time
            
            return embedding, processing_time
            
        except Exception as e:
            logger.error(f"OpenAI embedding generation failed: {e}")
            raise
    
    def generate_text_hash(self, text: str) -> str:
        """Generate hash for text caching"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def count_tokens(self, text: str) -> int:
        """Estimate token count for text"""
        # Simple approximation: ~4 characters per token
        return len(text) // 4
    
    def truncate_text(self, text: str, max_tokens: int) -> str:
        """Truncate text to fit within token limit"""
        if self.count_tokens(text) <= max_tokens:
            return text
        
        # Rough truncation based on character count
        max_chars = max_tokens * 4
        if len(text) <= max_chars:
            return text
        
        # Truncate and try to end at word boundary
        truncated = text[:max_chars]
        last_space = truncated.rfind(' ')
        if last_space > max_chars * 0.8:  # Only truncate at word boundary if it's not too far back
            truncated = truncated[:last_space]
        
        return truncated + "..." if truncated != text else text
    
    def generate_embedding_openai(self, text: str) -> tuple[List[float], float]:
        """Generate embedding using OpenAI API"""
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized")
        
        start_time = time.time()
        
        try:
            response = self.openai_client.embeddings.create(
                model=self.model_name,
                input=text,
                encoding_format="float"
            )
            
            embedding = response.data[0].embedding
            processing_time = time.time() - start_time
            
            return embedding, processing_time
            
        except Exception as e:
            logger.error(f"OpenAI embedding generation failed: {e}")
            raise
    
    def generate_embedding_fallback(self, text: str) -> tuple[List[float], float]:
        """Generate embedding using fallback model"""
        if not self.fallback_model:
            raise ValueError("Fallback model not initialized")
        
        start_time = time.time()
        
        try:
            embedding = self.fallback_model.encode(text, convert_to_numpy=True).tolist()
            processing_time = time.time() - start_time
            
            return embedding, processing_time
            
        except Exception as e:
            logger.error(f"Fallback embedding generation failed: {e}")
            raise
    
    def generate_embedding_mock(self, text: str) -> tuple[List[float], float]:
        """Generate mock embedding for testing"""
        start_time = time.time()
        
        # Generate deterministic but pseudo-random embedding based on text hash
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        seed = int(text_hash[:8], 16)
        
        import random
        random.seed(seed)
        
        # Generate embedding with correct dimension
        embedding = [random.uniform(-1, 1) for _ in range(self.dimension)]
        
        # Normalize embedding
        magnitude = sum(x*x for x in embedding) ** 0.5
        if magnitude > 0:
            embedding = [x/magnitude for x in embedding]
        
        processing_time = time.time() - start_time
        
        return embedding, processing_time
    
    def generate_single_embedding(self, text: str) -> EmbeddingResult:
        """Generate embedding for a single text"""
        start_time = time.time()
        
        try:
            # Check cache first
            if self.gemini_client:
                embedding, processing_time = self.generate_embedding_gemini(truncated_text)
                model_used = self.model_name
            elif self.cache_enabled and self.embedding_cache:
                text_hash = self.generate_text_hash(text)
                if text_hash in self.embedding_cache:
                    self.cache_hits += 1
                    cached_result = self.embedding_cache[text_hash]
                    return EmbeddingResult(
                        text=text,
                        embedding=cached_result['embedding'],
                        embedding_id=cached_result['id'],
                        model_used=cached_result['model'],
                        processing_time=0.001,  # Cache hit is very fast
                        token_count=cached_result['token_count'],
                        success=True
                    )
            
            # Truncate text if needed
            truncated_text = self.truncate_text(text, self.max_tokens)
            token_count = self.count_tokens(truncated_text)
            
            # Generate embedding
            if self.openai_client:
                embedding, processing_time = self.generate_embedding_openai(truncated_text)
                model_used = self.model_name
            elif self.fallback_model:
                embedding, processing_time = self.generate_embedding_fallback(truncated_text)
                model_used = "sentence-transformers"
            else:
                embedding, processing_time = self.generate_embedding_mock(truncated_text)
                model_used = "mock"
            
            # Create embedding ID
            embedding_id = f"emb_{int(time.time() * 1000)}_{hash(text) % 10000:04d}"
            
            # Cache result
            if self.cache_enabled and self.embedding_cache is not None:
                text_hash = self.generate_text_hash(text)
                self.embedding_cache[text_hash] = {
                    'embedding': embedding,
                    'id': embedding_id,
                    'model': model_used,
                    'token_count': token_count
                }
            
            # Update statistics
            self.total_embeddings += 1
            self.total_processing_time += processing_time
            
            return EmbeddingResult(
                text=text,
                embedding=embedding,
                embedding_id=embedding_id,
                model_used=model_used,
                processing_time=processing_time,
                token_count=token_count,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Failed to generate embedding for text: {e}")
            return EmbeddingResult(
                text=text,
                embedding=[],
                embedding_id="",
                model_used="",
                processing_time=time.time() - start_time,
                token_count=0,
                success=False,
                error_message=str(e)
            )
    
    def generate_batch_embeddings(self, texts: List[str]) -> List[EmbeddingResult]:
        """Generate embeddings for a batch of texts"""
        logger.info(f"Generating embeddings for batch of {len(texts)} texts")
        
        results = []
        
        # Process in batches
        for i in range(0, len(texts), self.batch_size):
            batch_texts = texts[i:i + self.batch_size]
            batch_start = time.time()
            
            # Process batch in parallel
            with ThreadPoolExecutor(max_workers=min(10, len(batch_texts))) as executor:
                future_to_text = {
                    executor.submit(self.generate_single_embedding, text): text 
                    for text in batch_texts
                }
                
                for future in as_completed(future_to_text):
                    text = future_to_text[future]
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        logger.error(f"Error in batch processing for text: {e}")
                        results.append(EmbeddingResult(
                            text=text,
                            embedding=[],
                            embedding_id="",
                            model_used="",
                            processing_time=0,
                            token_count=0,
                            success=False,
                            error_message=str(e)
                        ))
            
            batch_time = time.time() - batch_start
            logger.info(f"Batch {i//self.batch_size + 1} completed in {batch_time:.2f}s")
        
        # Log batch statistics
        successful = sum(1 for r in results if r.success)
        logger.info(f"Batch completed: {successful}/{len(results)} successful embeddings")
        
        return results
    
    def process_reviews_embeddings(self, processed_reviews: List) -> List[Dict]:
        """Generate embeddings for processed reviews"""
        logger.info(f"Processing embeddings for {len(processed_reviews)} reviews")
        
        # Extract texts from reviews
        texts = []
        review_mapping = []
        
        for i, review in enumerate(processed_reviews):
            if hasattr(review, 'cleaned_text') and review.cleaned_text:
                texts.append(review.cleaned_text)
                review_mapping.append(i)
        
        # Generate embeddings
        embedding_results = self.generate_batch_embeddings(texts)
        
        # Map results back to reviews
        reviews_with_embeddings = []
        
        for i, review in enumerate(processed_reviews):
            review_dict = {
                'external_review_id': review.external_review_id,
                'title': review.title,
                'review_text': review.review_text,
                'cleaned_text': review.cleaned_text,
                'author_name': review.author_name,
                'rating': review.rating,
                'review_date': review.review_date.isoformat(),
                'review_url': review.review_url,
                'version': review.version,
                'source': review.source,
                'product_id': review.product_id,
                'language': review.language,
                'sentiment_score': review.sentiment_score,
                'text_length': review.text_length,
                'word_count': review.word_count,
                'processed_at': review.processed_at.isoformat(),
                'status': review.status.value,
                'quality_score': review.quality_score
            }
            
            # Add embedding if available
            if i in review_mapping:
                embedding_index = review_mapping.index(i)
                if embedding_index < len(embedding_results):
                    embedding_result = embedding_results[embedding_index]
                    if embedding_result.success:
                        review_dict.update({
                            'embedding': embedding_result.embedding,
                            'embedding_id': embedding_result.embedding_id,
                            'embedding_model': embedding_result.model_used,
                            'embedding_time': embedding_result.processing_time,
                            'embedding_tokens': embedding_result.token_count
                        })
                    else:
                        review_dict.update({
                            'embedding': None,
                            'embedding_error': embedding_result.error_message
                        })
            
            reviews_with_embeddings.append(review_dict)
        
        return reviews_with_embeddings
    
    def get_statistics(self) -> Dict:
        """Get embedding service statistics"""
        stats = {
            'total_embeddings': self.total_embeddings,
            'total_processing_time': self.total_processing_time,
            'average_processing_time': 0,
            'cache_hits': self.cache_hits,
            'cache_hit_rate': 0,
            'cache_size': len(self.embedding_cache) if self.embedding_cache else 0,
            'model_used': self.model_name if self.openai_client else 
                         ("sentence-transformers" if self.fallback_model else "mock"),
            'dimension': self.dimension
        }
        
        if self.total_embeddings > 0:
            stats['average_processing_time'] = self.total_processing_time / self.total_embeddings
        
        if self.total_embeddings > 0:
            stats['cache_hit_rate'] = (self.cache_hits / self.total_embeddings) * 100
        
        return stats
    
    def clear_cache(self):
        """Clear embedding cache"""
        if self.embedding_cache:
            self.embedding_cache.clear()
            self.cache_hits = 0
            logger.info("Embedding cache cleared")
    
    def save_cache_to_file(self, filepath: str):
        """Save embedding cache to file"""
        if not self.embedding_cache:
            logger.warning("No cache to save")
            return
        
        try:
            with open(filepath, 'w') as f:
                json.dump(self.embedding_cache, f)
            logger.info(f"Cache saved to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    def load_cache_from_file(self, filepath: str):
        """Load embedding cache from file"""
        if not self.cache_enabled:
            logger.warning("Cache is disabled")
            return
        
        try:
            with open(filepath, 'r') as f:
                self.embedding_cache = json.load(f)
            logger.info(f"Cache loaded from {filepath}")
        except Exception as e:
            logger.error(f"Failed to load cache: {e}")


# Factory function
def create_embedding_service(config: dict) -> EmbeddingService:
    """Create EmbeddingService instance"""
    return EmbeddingService(config)
