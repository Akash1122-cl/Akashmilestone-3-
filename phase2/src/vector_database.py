"""
Vector Database Integration for Phase 2
Handles ChromaDB integration for storing and retrieving review embeddings
"""

import logging
import json
from typing import List, Dict, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import time
import hashlib
import os

# Try to import ChromaDB
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logging.warning("ChromaDB library not available, using mock vector database")

logger = logging.getLogger(__name__)


@dataclass
class VectorRecord:
    """Record for vector database storage"""
    id: str
    values: List[float]
    metadata: Dict[str, Union[str, int, float, bool]]
    namespace: str = "default"


@dataclass
class SearchResult:
    """Result from vector similarity search"""
    id: str
    score: float
    metadata: Dict[str, Union[str, int, float, bool]]
    values: Optional[List[float]] = None


@dataclass
class IndexStats:
    """Vector index statistics"""
    total_vector_count: int
    index_size: str
    dimension: int
    index_fullness: float
    namespaces: Dict[str, Dict[str, int]]


class VectorDatabase:
    """Vector database interface for storing and retrieving embeddings using ChromaDB"""
    
    def __init__(self, config: dict):
        self.config = config.get('vector_database', {})
        self.mode = self.config.get('mode', 'local')
        self.collection_name = self.config.get('collection_name', 'review-embeddings')
        self.dimension = self.config.get('dimension', 1536)
        self.metric = self.config.get('metric', 'cosine')
        self.persist_directory = self.config.get('persist_directory', './chroma_db')
        self.batch_size = self.config.get('batch_size', 100)
        self.cloud_config = self.config.get('cloud', {})
        
        # Initialize ChromaDB client
        self.client = None
        self.collection = None
        self.mock_db = None
        
        if CHROMADB_AVAILABLE:
            try:
                if self.mode == 'cloud':
                    self._initialize_cloud_client()
                else:
                    self._initialize_local_client()
                
                self._initialize_collection()
                logger.info(f"ChromaDB client initialized in {self.mode} mode with collection: {self.collection_name}")
            except Exception as e:
                logger.error(f"Failed to initialize ChromaDB client: {e}")
                self._initialize_mock_db()
        else:
            logger.info("Using mock vector database")
            self._initialize_mock_db()
    
    def _initialize_local_client(self):
        """Initialize local ChromaDB client"""
        try:
            # Create persist directory if it doesn't exist
            os.makedirs(self.persist_directory, exist_ok=True)
            
            # Initialize ChromaDB client with persistence
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
        except Exception as e:
            logger.error(f"Failed to initialize local ChromaDB client: {e}")
            raise
    
    def _initialize_cloud_client(self):
        """Initialize Chroma Cloud client"""
        try:
            api_key = self.cloud_config.get('api_key')
            tenant_id = self.cloud_config.get('tenant_id')
            host = self.cloud_config.get('host')
            
            # Clean up values (remove quotes if present)
            if api_key:
                api_key = api_key.strip().strip("'").strip('"')
            if tenant_id:
                tenant_id = tenant_id.strip().strip("'").strip('"')
            if host:
                host = host.strip().strip("'").strip('"')
            
            if not api_key:
                raise ValueError("Chroma Cloud API key not configured")
            
            if not tenant_id:
                raise ValueError("Chroma Cloud tenant ID not configured")
            
            if not host:
                raise ValueError("Chroma Cloud host not configured")
            
            # Try different Chroma Cloud authentication methods
            try:
                # Method 1: Standard Chroma Cloud authentication
                self.client = chromadb.HttpClient(
                    host=host,
                    headers={
                        'Authorization': f'Bearer {api_key}',
                        'X-Chroma-Tenant': tenant_id
                    },
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )
                logger.info(f"Chroma Cloud client initialized using standard auth for host: {host}")
            except Exception as e1:
                logger.warning(f"Standard auth failed, trying alternative method: {e1}")
                # Method 2: Alternative authentication
                try:
                    self.client = chromadb.HttpClient(
                        host=host,
                        headers={
                            'X-Chroma-Token': api_key,
                            'X-Chroma-Tenant': tenant_id
                        },
                        settings=Settings(
                            anonymized_telemetry=False,
                            allow_reset=True
                        )
                    )
                    logger.info(f"Chroma Cloud client initialized using alternative auth for host: {host}")
                except Exception as e2:
                    logger.error(f"All Chroma Cloud authentication methods failed: {e2}")
                    raise
            
            # Test connection by listing collections
            self.client.list_collections()
            logger.info("Chroma Cloud connection test successful")
            
        except Exception as e:
            logger.error(f"Failed to initialize Chroma Cloud client: {e}")
            raise
    
    def _initialize_collection(self):
        """Initialize ChromaDB collection"""
        try:
            # Check if collection exists
            existing_collections = [col.name for col in self.client.list_collections()]
            
            if self.collection_name not in existing_collections:
                # Create new collection
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": self.metric}
                )
                logger.info(f"Created new ChromaDB collection: {self.collection_name}")
            else:
                # Get existing collection
                self.collection = self.client.get_collection(name=self.collection_name)
                logger.info(f"Connected to existing ChromaDB collection: {self.collection_name}")
                
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB collection: {e}")
            raise
    
    def _initialize_mock_db(self):
        """Initialize mock vector database for testing"""
        self.mock_db = {
            'vectors': {},
            'metadata': {},
            'ids': [],
            'stats': {
                'total_vectors': 0,
                'dimension': self.dimension
            }
        }
        logger.info("Mock vector database initialized")
    
    def generate_vector_id(self, review_data: Dict) -> str:
        """Generate unique vector ID for review"""
        # Use external review ID with hash for uniqueness
        external_id = review_data.get('external_review_id', '')
        source = review_data.get('source', '')
        product_id = review_data.get('product_id', 0)
        
        id_string = f"{source}_{product_id}_{external_id}"
        hash_value = hashlib.md5(id_string.encode('utf-8')).hexdigest()[:8]
        
        return f"vec_{hash_value}"
    
    def upsert_vectors(self, vectors: List[VectorRecord]) -> bool:
        """Upsert vectors to database"""
        try:
            if self.client and self.collection:
                return self._upsert_chromadb(vectors)
            elif self.mock_db:
                return self._upsert_mock(vectors)
            else:
                logger.error("No vector database available")
                return False
        except Exception as e:
            logger.error(f"Failed to upsert vectors: {e}")
            return False
    
    def _upsert_chromadb(self, vectors: List[VectorRecord]) -> bool:
        """Upsert vectors to ChromaDB"""
        try:
            # Prepare vectors for ChromaDB
            ids = []
            embeddings = []
            metadatas = []
            
            for vector in vectors:
                ids.append(vector.id)
                embeddings.append(vector.values)
                metadatas.append(vector.metadata)
            
            # Upsert in batches
            for i in range(0, len(ids), self.batch_size):
                batch_ids = ids[i:i + self.batch_size]
                batch_embeddings = embeddings[i:i + self.batch_size]
                batch_metadatas = metadatas[i:i + self.batch_size]
                
                self.collection.upsert(
                    ids=batch_ids,
                    embeddings=batch_embeddings,
                    metadatas=batch_metadatas
                )
                
                logger.info(f"Upserted batch {i//self.batch_size + 1} with {len(batch_ids)} vectors")
            
            logger.info(f"Successfully upserted {len(vectors)} vectors to ChromaDB")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upsert to ChromaDB: {e}")
            return False
    
    def _upsert_mock(self, vectors: List[VectorRecord]) -> bool:
        """Upsert vectors to mock database"""
        try:
            for vector in vectors:
                self.mock_db['vectors'][vector.id] = vector.values
                self.mock_db['metadata'][vector.id] = vector.metadata
                self.mock_db['stats']['total_vectors'] += 1
            
            logger.info(f"Successfully upserted {len(vectors)} vectors to mock DB")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upsert to mock DB: {e}")
            return False
    
    def search_similar(self, query_vector: List[float], top_k: int = 10, 
                      filter_dict: Optional[Dict] = None) -> List[SearchResult]:
        """Search for similar vectors"""
        try:
            if self.pinecone_client and self.index:
                return self._search_pinecone(query_vector, top_k, filter_dict)
            elif self.mock_db:
                return self._search_mock(query_vector, top_k, filter_dict)
            else:
                logger.error("No vector database available")
                return []
        except Exception as e:
            logger.error(f"Failed to search vectors: {e}")
            return []
    
    def _search_pinecone(self, query_vector: List[float], top_k: int, 
                        filter_dict: Optional[Dict] = None) -> List[SearchResult]:
        """Search similar vectors in Pinecone"""
        try:
            # Prepare search parameters
            search_params = {
                'vector': query_vector,
                'top_k': top_k,
                'namespace': self.namespace,
                'include_metadata': True
            }
            
            if filter_dict:
                search_params['filter'] = filter_dict
            
            # Perform search
            results = self.index.query(**search_params)
            
            # Convert to SearchResult objects
            search_results = []
            for match in results['matches']:
                search_results.append(SearchResult(
                    id=match['id'],
                    score=match['score'],
                    metadata=match.get('metadata', {}),
                    values=match.get('values')
                ))
            
            logger.info(f"Found {len(search_results)} similar vectors in Pinecone")
            return search_results
            
        except Exception as e:
            logger.error(f"Failed to search Pinecone: {e}")
            return []
    
    def _search_mock(self, query_vector: List[float], top_k: int, 
                    filter_dict: Optional[Dict] = None) -> List[SearchResult]:
        """Search similar vectors in mock database (simple cosine similarity)"""
        try:
            results = []
            
            for vector_id, stored_vector in self.mock_db['vectors'].items():
                # Apply filter if provided
                if filter_dict:
                    metadata = self.mock_db['metadata'].get(vector_id, {})
                    if not self._matches_filter(metadata, filter_dict):
                        continue
                
                # Calculate cosine similarity
                similarity = self._cosine_similarity(query_vector, stored_vector)
                
                results.append(SearchResult(
                    id=vector_id,
                    score=similarity,
                    metadata=self.mock_db['metadata'].get(vector_id, {}),
                    values=stored_vector
                ))
            
            # Sort by similarity and return top_k
            results.sort(key=lambda x: x.score, reverse=True)
            results = results[:top_k]
            
            logger.info(f"Found {len(results)} similar vectors in mock DB")
            return results
            
        except Exception as e:
            logger.error(f"Failed to search mock DB: {e}")
            return []
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            import math
            
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            magnitude1 = math.sqrt(sum(a * a for a in vec1))
            magnitude2 = math.sqrt(sum(b * b for b in vec2))
            
            if magnitude1 == 0 or magnitude2 == 0:
                return 0.0
            
            return dot_product / (magnitude1 * magnitude2)
            
        except Exception:
            return 0.0
    
    def _matches_filter(self, metadata: Dict, filter_dict: Dict) -> bool:
        """Check if metadata matches filter"""
        for key, value in filter_dict.items():
            if key not in metadata or metadata[key] != value:
                return False
        return True
    
    def get_vector_by_id(self, vector_id: str) -> Optional[VectorRecord]:
        """Get vector by ID"""
        try:
            if self.pinecone_client and self.index:
                return self._get_vector_pinecone(vector_id)
            elif self.mock_db:
                return self._get_vector_mock(vector_id)
            else:
                return None
        except Exception as e:
            logger.error(f"Failed to get vector {vector_id}: {e}")
            return None
    
    def _get_vector_pinecone(self, vector_id: str) -> Optional[VectorRecord]:
        """Get vector from Pinecone"""
        try:
            result = self.index.fetch(ids=[vector_id], namespace=self.namespace)
            
            if vector_id in result['vectors']:
                vector_data = result['vectors'][vector_id]
                return VectorRecord(
                    id=vector_id,
                    values=vector_data['values'],
                    metadata=vector_data.get('metadata', {}),
                    namespace=self.namespace
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get vector from Pinecone: {e}")
            return None
    
    def _get_vector_mock(self, vector_id: str) -> Optional[VectorRecord]:
        """Get vector from mock database"""
        try:
            if vector_id in self.mock_db['vectors']:
                return VectorRecord(
                    id=vector_id,
                    values=self.mock_db['vectors'][vector_id],
                    metadata=self.mock_db['metadata'].get(vector_id, {}),
                    namespace=self.namespace
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get vector from mock DB: {e}")
            return None
    
    def delete_vectors(self, vector_ids: List[str]) -> bool:
        """Delete vectors from database"""
        try:
            if self.pinecone_client and self.index:
                return self._delete_pinecone(vector_ids)
            elif self.mock_db:
                return self._delete_mock(vector_ids)
            else:
                logger.error("No vector database available")
                return False
        except Exception as e:
            logger.error(f"Failed to delete vectors: {e}")
            return False
    
    def _delete_pinecone(self, vector_ids: List[str]) -> bool:
        """Delete vectors from Pinecone"""
        try:
            self.index.delete(ids=vector_ids, namespace=self.namespace)
            logger.info(f"Deleted {len(vector_ids)} vectors from Pinecone")
            return True
        except Exception as e:
            logger.error(f"Failed to delete from Pinecone: {e}")
            return False
    
    def _delete_mock(self, vector_ids: List[str]) -> bool:
        """Delete vectors from mock database"""
        try:
            for vector_id in vector_ids:
                self.mock_db['vectors'].pop(vector_id, None)
                self.mock_db['metadata'].pop(vector_id, None)
                self.mock_db['stats']['total_vectors'] = max(0, 
                    self.mock_db['stats']['total_vectors'] - 1)
            
            logger.info(f"Deleted {len(vector_ids)} vectors from mock DB")
            return True
        except Exception as e:
            logger.error(f"Failed to delete from mock DB: {e}")
            return False
    
    def get_index_stats(self) -> IndexStats:
        """Get index statistics"""
        try:
            if self.pinecone_client and self.index:
                return self._get_stats_pinecone()
            elif self.mock_db:
                return self._get_stats_mock()
            else:
                return IndexStats(0, "0B", 0, 0.0, {})
        except Exception as e:
            logger.error(f"Failed to get index stats: {e}")
            return IndexStats(0, "0B", 0, 0.0, {})
    
    def _get_stats_pinecone(self) -> IndexStats:
        """Get Pinecone index statistics"""
        try:
            stats = self.index.describe_index_stats()
            
            return IndexStats(
                total_vector_count=stats['totalVectorCount'],
                index_size=stats.get('indexSize', 'Unknown'),
                dimension=stats['dimension'],
                index_fullness=stats.get('indexFullness', 0.0),
                namespaces=stats.get('namespaces', {})
            )
        except Exception as e:
            logger.error(f"Failed to get Pinecone stats: {e}")
            return IndexStats(0, "0B", 0, 0.0, {})
    
    def _get_stats_mock(self) -> IndexStats:
        """Get mock database statistics"""
        return IndexStats(
            total_vector_count=self.mock_db['stats']['total_vectors'],
            index_size=f"{len(str(self.mock_db))}B",
            dimension=self.mock_db['stats']['dimension'],
            index_fullness=1.0,
            namespaces={self.namespace: {'vector_count': self.mock_db['stats']['total_vectors']}}
        )
    
    def create_index_from_reviews(self, reviews: List[Dict]) -> bool:
        """Create vector index from processed reviews with embeddings"""
        try:
            logger.info(f"Creating vector index from {len(reviews)} reviews")
            
            # Prepare vectors
            vectors = []
            for review in reviews:
                if review.get('embedding'):
                    vector_id = self.generate_vector_id(review)
                    
                    # Prepare metadata
                    metadata = {
                        'external_review_id': review.get('external_review_id'),
                        'title': review.get('title', ''),
                        'author_name': review.get('author_name', ''),
                        'rating': review.get('rating', 0),
                        'review_date': review.get('review_date', ''),
                        'source': review.get('source', ''),
                        'product_id': review.get('product_id', 0),
                        'language': review.get('language', ''),
                        'sentiment_score': review.get('sentiment_score', 0),
                        'quality_score': review.get('quality_score', 0),
                        'text_length': review.get('text_length', 0),
                        'word_count': review.get('word_count', 0),
                        'processed_at': review.get('processed_at', '')
                    }
                    
                    vectors.append(VectorRecord(
                        id=vector_id,
                        values=review['embedding'],
                        metadata=metadata,
                        namespace=self.namespace
                    ))
            
            # Upsert vectors
            success = self.upsert_vectors(vectors)
            
            if success:
                logger.info(f"Successfully created vector index with {len(vectors)} vectors")
                
                # Get index statistics
                stats = self.get_index_stats()
                logger.info(f"Index stats: {stats.total_vector_count} vectors, {stats.index_size}")
                
                return True
            else:
                logger.error("Failed to create vector index")
                return False
                
        except Exception as e:
            logger.error(f"Failed to create index from reviews: {e}")
            return False
    
    def search_reviews_by_embedding(self, query_text: str, embedding_service, 
                                   top_k: int = 10) -> List[SearchResult]:
        """Search reviews by text embedding"""
        try:
            # Generate embedding for query text
            embedding_result = embedding_service.generate_single_embedding(query_text)
            
            if not embedding_result.success:
                logger.error("Failed to generate embedding for query")
                return []
            
            # Search similar vectors
            return self.search_similar(embedding_result.embedding, top_k)
            
        except Exception as e:
            logger.error(f"Failed to search reviews by embedding: {e}")
            return []
    
    def find_similar_reviews(self, review_id: str, top_k: int = 10) -> List[SearchResult]:
        """Find similar reviews to a given review"""
        try:
            # Get the review vector
            vector_record = self.get_vector_by_id(review_id)
            
            if not vector_record:
                logger.error(f"Review {review_id} not found in vector database")
                return []
            
            # Search for similar vectors
            return self.search_similar(vector_record.values, top_k)
            
        except Exception as e:
            logger.error(f"Failed to find similar reviews for {review_id}: {e}")
            return []


# Factory function
def create_vector_database(config: dict) -> VectorDatabase:
    """Create VectorDatabase instance"""
    return VectorDatabase(config)
