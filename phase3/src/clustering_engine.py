"""
Clustering Engine for Phase 3
Implements UMAP dimensionality reduction and HDBSCAN clustering for theme detection
"""

import logging
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import json

# Try to import ML libraries
try:
    import umap
    import hdbscan
    from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    logging.warning("ML libraries not available, using mock clustering")

logger = logging.getLogger(__name__)


@dataclass
class ClusterResult:
    """Result from clustering operation"""
    cluster_id: int
    cluster_size: int
    cluster_labels: List[int]
    cluster_centers: Optional[np.ndarray]
    cluster_metadata: Dict[str, Any]
    quality_metrics: Dict[str, float]


@dataclass
class ClusteringMetrics:
    """Quality metrics for clustering"""
    silhouette_score: float
    davies_bouldin_score: float
    calinski_harabasz_score: float
    num_clusters: int
    noise_points: int
    total_points: int


class ClusteringEngine:
    """Clustering engine using UMAP + HDBSCAN for theme detection"""
    
    def __init__(self, config: dict):
        self.config = config.get('clustering', {})
        self.umap_config = self.config.get('umap', {})
        self.hdbscan_config = self.config.get('hdbscan', {})
        self.optimization_config = self.config.get('optimization', {})
        self.quality_config = self.config.get('quality_metrics', {})
        
        # Initialize models
        self.umap_model = None
        self.hdbscan_model = None
        self.mock_mode = False
        
        if not ML_AVAILABLE:
            logger.info("Using mock clustering mode")
            self.mock_mode = True
        else:
            self._initialize_models()
    
    def _initialize_models(self):
        """Initialize UMAP and HDBSCAN models"""
        try:
            # Initialize UMAP
            self.umap_model = umap.UMAP(
                n_components=self.umap_config.get('n_components', 15),
                n_neighbors=self.umap_config.get('n_neighbors', 15),
                min_dist=self.umap_config.get('min_dist', 0.1),
                metric=self.umap_config.get('metric', 'cosine'),
                random_state=self.umap_config.get('random_state', 42)
            )
            
            # Initialize HDBSCAN
            self.hdbscan_model = hdbscan.HDBSCAN(
                min_cluster_size=self.hdbscan_config.get('min_cluster_size', 5),
                min_samples=self.hdbscan_config.get('min_samples', 3),
                metric=self.hdbscan_config.get('metric', 'euclidean'),
                cluster_selection_method=self.hdbscan_config.get('cluster_selection_method', 'eom'),
                prediction_data=self.hdbscan_config.get('prediction_data', True)
            )
            
            logger.info("UMAP and HDBSCAN models initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize ML models: {e}")
            self.mock_mode = True
    
    def cluster_reviews(self, embeddings: List[List[float]], 
                       review_ids: List[str]) -> ClusterResult:
        """
        Cluster review embeddings using UMAP + HDBSCAN
        
        Args:
            embeddings: List of embedding vectors
            review_ids: List of review IDs corresponding to embeddings
            
        Returns:
            ClusterResult with clustering information
        """
        try:
            if self.mock_mode:
                return self._cluster_mock(embeddings, review_ids)
            
            logger.info(f"Clustering {len(embeddings)} reviews")
            
            # Convert to numpy array
            embeddings_array = np.array(embeddings)
            
            # Apply UMAP dimensionality reduction
            reduced_embeddings = self.umap_model.fit_transform(embeddings_array)
            logger.info(f"Reduced embeddings from {embeddings_array.shape} to {reduced_embeddings.shape}")
            
            # Apply HDBSCAN clustering
            cluster_labels = self.hdbscan_model.fit_predict(reduced_embeddings)
            
            # Calculate cluster metrics
            num_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
            noise_points = list(cluster_labels).count(-1)
            
            logger.info(f"Found {num_clusters} clusters with {noise_points} noise points")
            
            # Calculate cluster centers
            cluster_centers = self._calculate_cluster_centers(
                reduced_embeddings, cluster_labels, num_clusters
            )
            
            # Calculate quality metrics
            quality_metrics = self._calculate_quality_metrics(
                reduced_embeddings, cluster_labels
            )
            
            # Build cluster metadata
            cluster_metadata = {
                'num_clusters': num_clusters,
                'noise_points': noise_points,
                'total_points': len(embeddings),
                'cluster_sizes': self._get_cluster_sizes(cluster_labels),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            return ClusterResult(
                cluster_id=0,  # Single clustering operation
                cluster_size=len(embeddings),
                cluster_labels=cluster_labels.tolist(),
                cluster_centers=cluster_centers.tolist() if cluster_centers is not None else None,
                cluster_metadata=cluster_metadata,
                quality_metrics=quality_metrics
            )
            
        except Exception as e:
            logger.error(f"Failed to cluster reviews: {e}")
            raise
    
    def _cluster_mock(self, embeddings: List[List[float]], 
                     review_ids: List[str]) -> ClusterResult:
        """Mock clustering for testing without ML libraries"""
        try:
            num_reviews = len(embeddings)
            # Simple mock: assign clusters based on index ranges
            cluster_labels = []
            num_clusters = max(3, min(7, num_reviews // 10))
            
            for i in range(num_reviews):
                cluster_labels.append(i % num_clusters)
            
            cluster_labels = np.array(cluster_labels)
            
            cluster_metadata = {
                'num_clusters': num_clusters,
                'noise_points': 0,
                'total_points': num_reviews,
                'cluster_sizes': {i: list(cluster_labels).count(i) for i in range(num_clusters)},
                'timestamp': datetime.utcnow().isoformat(),
                'mock_mode': True
            }
            
            quality_metrics = {
                'silhouette_score': 0.5,
                'davies_bouldin_score': 1.0,
                'calinski_harabasz_score': 100.0
            }
            
            return ClusterResult(
                cluster_id=0,
                cluster_size=num_reviews,
                cluster_labels=cluster_labels.tolist(),
                cluster_centers=None,
                cluster_metadata=cluster_metadata,
                quality_metrics=quality_metrics
            )
            
        except Exception as e:
            logger.error(f"Failed to perform mock clustering: {e}")
            raise
    
    def _calculate_cluster_centers(self, embeddings: np.ndarray, 
                                   labels: np.ndarray, 
                                   num_clusters: int) -> Optional[np.ndarray]:
        """Calculate cluster centers"""
        try:
            if num_clusters == 0:
                return None
            
            centers = []
            for cluster_id in range(num_clusters):
                cluster_mask = labels == cluster_id
                if np.any(cluster_mask):
                    center = np.mean(embeddings[cluster_mask], axis=0)
                    centers.append(center)
            
            return np.array(centers) if centers else None
            
        except Exception as e:
            logger.error(f"Failed to calculate cluster centers: {e}")
            return None
    
    def _get_cluster_sizes(self, labels: np.ndarray) -> Dict[int, int]:
        """Get size of each cluster"""
        unique_labels, counts = np.unique(labels, return_counts=True)
        return dict(zip(unique_labels.tolist(), counts.tolist()))
    
    def _calculate_quality_metrics(self, embeddings: np.ndarray, 
                                   labels: np.ndarray) -> Dict[str, float]:
        """Calculate clustering quality metrics"""
        metrics = {}
        
        try:
            # Filter out noise points for metrics calculation
            non_noise_mask = labels != -1
            if np.sum(non_noise_mask) < 2:
                logger.warning("Not enough non-noise points for quality metrics")
                return {
                    'silhouette_score': 0.0,
                    'davies_bouldin_score': float('inf'),
                    'calinski_harabasz_score': 0.0
                }
            
            embeddings_filtered = embeddings[non_noise_mask]
            labels_filtered = labels[non_noise_mask]
            
            # Silhouette score (higher is better, range -1 to 1)
            if self.quality_config.get('silhouette_score', True):
                try:
                    metrics['silhouette_score'] = silhouette_score(
                        embeddings_filtered, labels_filtered
                    )
                except Exception as e:
                    logger.warning(f"Failed to calculate silhouette score: {e}")
                    metrics['silhouette_score'] = 0.0
            
            # Davies-Bouldin index (lower is better)
            if self.quality_config.get('davies_bouldin_index', True):
                try:
                    if len(set(labels_filtered)) > 1:
                        metrics['davies_bouldin_score'] = davies_bouldin_score(
                            embeddings_filtered, labels_filtered
                        )
                    else:
                        metrics['davies_bouldin_score'] = 0.0
                except Exception as e:
                    logger.warning(f"Failed to calculate Davies-Bouldin score: {e}")
                    metrics['davies_bouldin_score'] = float('inf')
            
            # Calinski-Harabasz index (higher is better)
            if self.quality_config.get('calinski_harabasz_index', True):
                try:
                    if len(set(labels_filtered)) > 1:
                        metrics['calinski_harabasz_score'] = calinski_harabasz_score(
                            embeddings_filtered, labels_filtered
                        )
                    else:
                        metrics['calinski_harabasz_score'] = 0.0
                except Exception as e:
                    logger.warning(f"Failed to calculate Calinski-Harabasz score: {e}")
                    metrics['calinski_harabasz_score'] = 0.0
            
        except Exception as e:
            logger.error(f"Failed to calculate quality metrics: {e}")
        
        return metrics
    
    def optimize_parameters(self, embeddings: List[List[float]], 
                           review_ids: List[str]) -> Dict[str, Any]:
        """
        Optimize clustering parameters to achieve target cluster count
        
        Args:
            embeddings: List of embedding vectors
            review_ids: List of review IDs
            
        Returns:
            Dictionary with best parameters and results
        """
        if not self.optimization_config.get('enabled', False):
            logger.info("Parameter optimization disabled, using default parameters")
            return {
                'optimized': False,
                'parameters': self.umap_config.copy()
            }
        
        if self.mock_mode:
            logger.info("Mock mode: skipping parameter optimization")
            return {
                'optimized': False,
                'parameters': self.umap_config.copy(),
                'mock_mode': True
            }
        
        try:
            logger.info("Starting parameter optimization")
            
            best_result = None
            best_score = -1
            best_params = {}
            
            target_clusters = self.optimization_config.get('target_clusters', [5, 7])
            max_iterations = self.optimization_config.get('max_iterations', 10)
            
            embeddings_array = np.array(embeddings)
            
            for iteration in range(max_iterations):
                # Sample parameters
                n_neighbors = np.random.randint(5, 30)
                min_cluster_size = np.random.randint(3, 15)
                min_dist = np.random.uniform(0.0, 0.3)
                
                # Create temporary models
                temp_umap = umap.UMAP(
                    n_components=self.umap_config.get('n_components', 15),
                    n_neighbors=n_neighbors,
                    min_dist=min_dist,
                    metric=self.umap_config.get('metric', 'cosine'),
                    random_state=42
                )
                
                temp_hdbscan = hdbscan.HDBSCAN(
                    min_cluster_size=min_cluster_size,
                    min_samples=self.hdbscan_config.get('min_samples', 3),
                    metric=self.hdbscan_config.get('metric', 'euclidean'),
                    cluster_selection_method=self.hdbscan_config.get('cluster_selection_method', 'eom')
                )
                
                # Perform clustering
                reduced = temp_umap.fit_transform(embeddings_array)
                labels = temp_hdbscan.fit_predict(reduced)
                
                num_clusters = len(set(labels)) - (1 if -1 in labels else 0)
                
                # Calculate score based on target cluster count
                if target_clusters[0] <= num_clusters <= target_clusters[1]:
                    try:
                        score = silhouette_score(reduced[labels != -1], labels[labels != -1])
                    except:
                        score = 0.0
                    
                    if score > best_score:
                        best_score = score
                        best_params = {
                            'n_neighbors': n_neighbors,
                            'min_cluster_size': min_cluster_size,
                            'min_dist': min_dist
                        }
                        best_result = {
                            'num_clusters': num_clusters,
                            'silhouette_score': score
                        }
                
                logger.info(f"Iteration {iteration + 1}/{max_iterations}: "
                          f"n_neighbors={n_neighbors}, min_cluster_size={min_cluster_size}, "
                          f"clusters={num_clusters}, score={score:.3f}")
            
            if best_params:
                logger.info(f"Best parameters found: {best_params}")
                # Update models with best parameters
                self.umap_model = umap.UMAP(
                    n_components=self.umap_config.get('n_components', 15),
                    n_neighbors=best_params['n_neighbors'],
                    min_dist=best_params['min_dist'],
                    metric=self.umap_config.get('metric', 'cosine'),
                    random_state=42
                )
                self.hdbscan_model = hdbscan.HDBSCAN(
                    min_cluster_size=best_params['min_cluster_size'],
                    min_samples=self.hdbscan_config.get('min_samples', 3),
                    metric=self.hdbscan_config.get('metric', 'euclidean'),
                    cluster_selection_method=self.hdbscan_config.get('cluster_selection_method', 'eom')
                )
                
                return {
                    'optimized': True,
                    'parameters': best_params,
                    'result': best_result
                }
            else:
                logger.warning("No suitable parameters found within target range")
                return {
                    'optimized': False,
                    'parameters': self.umap_config.copy()
                }
                
        except Exception as e:
            logger.error(f"Parameter optimization failed: {e}")
            return {
                'optimized': False,
                'parameters': self.umap_config.copy(),
                'error': str(e)
            }
    
    def get_cluster_reviews(self, cluster_result: ClusterResult, 
                           cluster_id: int, 
                           review_ids: List[str]) -> List[str]:
        """
        Get review IDs belonging to a specific cluster
        
        Args:
            cluster_result: Result from clustering operation
            cluster_id: ID of the cluster to query
            review_ids: List of all review IDs
            
        Returns:
            List of review IDs in the cluster
        """
        try:
            labels = np.array(cluster_result.cluster_labels)
            cluster_mask = labels == cluster_id
            cluster_review_ids = [review_ids[i] for i in range(len(review_ids)) if cluster_mask[i]]
            
            logger.info(f"Cluster {cluster_id} contains {len(cluster_review_ids)} reviews")
            return cluster_review_ids
            
        except Exception as e:
            logger.error(f"Failed to get cluster reviews: {e}")
            return []


# Factory function
def create_clustering_engine(config: dict) -> ClusteringEngine:
    """Create ClusteringEngine instance"""
    return ClusteringEngine(config)
