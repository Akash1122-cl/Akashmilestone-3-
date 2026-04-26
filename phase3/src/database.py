"""
Database operations for Phase 3
Handles storage and retrieval of analysis results, themes, and validation data
"""

import logging
import json
from typing import List, Dict, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict

import psycopg2
from psycopg2.extras import Json, RealDictCursor
from psycopg2.pool import SimpleConnectionPool

logger = logging.getLogger(__name__)


@dataclass
class AnalysisRun:
    """Represents an analysis run"""
    id: Optional[int]
    product_id: int
    product_name: str
    analysis_timestamp: str
    total_reviews: int
    num_clusters: int
    num_themes: int
    processing_time_seconds: float
    clustering_quality_metrics: Dict[str, float]
    validation_result: Dict[str, Any]
    status: str


class Phase3Database:
    """Database operations for Phase 3 analysis results"""
    
    def __init__(self, config: dict):
        self.config = config.get('database', {})
        self.host = self.config.get('host', 'localhost')
        self.port = self.config.get('port', 5432)
        self.database = self.config.get('database', 'review_pulse')
        self.username = self.config.get('username', 'postgres')
        self.password = self.config.get('password', '')
        self.pool_size = self.config.get('pool_size', 10)
        
        self.pool = None
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize database connection pool"""
        try:
            self.pool = SimpleConnectionPool(
                minconn=1,
                maxconn=self.pool_size,
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.username,
                password=self.password
            )
            logger.info("Database connection pool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise
    
    def _get_connection(self):
        """Get connection from pool"""
        return self.pool.getconn()
    
    def _return_connection(self, conn):
        """Return connection to pool"""
        self.pool.putconn(conn)
    
    def save_analysis_run(self, analysis_run: AnalysisRun) -> int:
        """
        Save analysis run to database
        
        Args:
            analysis_run: AnalysisRun object to save
            
        Returns:
            ID of the inserted analysis run
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                query = """
                    INSERT INTO analysis_runs (
                        product_id, product_name, analysis_timestamp, total_reviews,
                        num_clusters, num_themes, processing_time_seconds,
                        clustering_quality_metrics, validation_result, status
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """
                
                cursor.execute(query, (
                    analysis_run.product_id,
                    analysis_run.product_name,
                    analysis_run.analysis_timestamp,
                    analysis_run.total_reviews,
                    analysis_run.num_clusters,
                    analysis_run.num_themes,
                    analysis_run.processing_time_seconds,
                    Json(analysis_run.clustering_quality_metrics),
                    Json(analysis_run.validation_result),
                    analysis_run.status
                ))
                
                analysis_run_id = cursor.fetchone()[0]
                conn.commit()
                
                logger.info(f"Saved analysis run {analysis_run_id}")
                return analysis_run_id
                
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to save analysis run: {e}")
            raise
        finally:
            self._return_connection(conn)
    
    def save_themes(self, analysis_run_id: int, themes: List[Dict]) -> bool:
        """
        Save themes to database
        
        Args:
            analysis_run_id: ID of the analysis run
            themes: List of theme dictionaries
            
        Returns:
            True if successful, False otherwise
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                query = """
                    INSERT INTO themes (
                        analysis_run_id, theme_id, name, description, cluster_id,
                        cluster_size, sentiment_score, quality_score,
                        representative_quotes, action_ideas, metadata
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                for theme in themes:
                    cursor.execute(query, (
                        analysis_run_id,
                        theme.get('theme_id'),
                        theme.get('name'),
                        theme.get('description'),
                        theme.get('cluster_id'),
                        theme.get('cluster_size'),
                        theme.get('sentiment_score', 0.5),
                        theme.get('quality_score', 0.5),
                        Json(theme.get('representative_quotes', [])),
                        Json(theme.get('action_ideas', [])),
                        Json(theme.get('metadata', {}))
                    ))
                
                conn.commit()
                logger.info(f"Saved {len(themes)} themes for analysis run {analysis_run_id}")
                return True
                
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to save themes: {e}")
            return False
        finally:
            self._return_connection(conn)
    
    def save_cluster_assignments(self, analysis_run_id: int, 
                                 cluster_labels: List[int],
                                 review_ids: List[str]) -> bool:
        """
        Save cluster assignments to database
        
        Args:
            analysis_run_id: ID of the analysis run
            cluster_labels: List of cluster labels
            review_ids: List of review IDs
            
        Returns:
            True if successful, False otherwise
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                query = """
                    INSERT INTO cluster_assignments (
                        analysis_run_id, review_id, cluster_id, is_noise
                    ) VALUES (%s, %s, %s, %s)
                """
                
                for review_id, cluster_id in zip(review_ids, cluster_labels):
                    is_noise = cluster_id == -1
                    cursor.execute(query, (
                        analysis_run_id,
                        review_id,
                        cluster_id,
                        is_noise
                    ))
                
                conn.commit()
                logger.info(f"Saved {len(review_ids)} cluster assignments for analysis run {analysis_run_id}")
                return True
                
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to save cluster assignments: {e}")
            return False
        finally:
            self._return_connection(conn)
    
    def save_validation_result(self, analysis_run_id: int, 
                              validation_result: Dict) -> bool:
        """
        Save validation result to database
        
        Args:
            analysis_run_id: ID of the analysis run
            validation_result: Validation result dictionary
            
        Returns:
            True if successful, False otherwise
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                query = """
                    INSERT INTO validation_results (
                        analysis_run_id, is_valid, quote_accuracy_score,
                        theme_coherence_score, action_relevance_score,
                        overall_quality_score, validation_errors,
                        validation_warnings, metadata
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (analysis_run_id) DO UPDATE SET
                        is_valid = EXCLUDED.is_valid,
                        quote_accuracy_score = EXCLUDED.quote_accuracy_score,
                        theme_coherence_score = EXCLUDED.theme_coherence_score,
                        action_relevance_score = EXCLUDED.action_relevance_score,
                        overall_quality_score = EXCLUDED.overall_quality_score,
                        validation_errors = EXCLUDED.validation_errors,
                        validation_warnings = EXCLUDED.validation_warnings,
                        metadata = EXCLUDED.metadata
                """
                
                cursor.execute(query, (
                    analysis_run_id,
                    validation_result.get('is_valid', False),
                    validation_result.get('quote_accuracy_score', 0.0),
                    validation_result.get('theme_coherence_score', 0.0),
                    validation_result.get('action_relevance_score', 0.0),
                    validation_result.get('overall_quality_score', 0.0),
                    Json(validation_result.get('validation_errors', [])),
                    Json(validation_result.get('validation_warnings', [])),
                    Json(validation_result.get('metadata', {}))
                ))
                
                conn.commit()
                logger.info(f"Saved validation result for analysis run {analysis_run_id}")
                return True
                
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to save validation result: {e}")
            return False
        finally:
            self._return_connection(conn)
    
    def get_analysis_run(self, analysis_run_id: int) -> Optional[Dict]:
        """
        Get analysis run by ID
        
        Args:
            analysis_run_id: ID of the analysis run
            
        Returns:
            Analysis run dictionary or None
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                query = """
                    SELECT * FROM analysis_runs WHERE id = %s
                """
                cursor.execute(query, (analysis_run_id,))
                result = cursor.fetchone()
                
                if result:
                    return dict(result)
                return None
                
        except Exception as e:
            logger.error(f"Failed to get analysis run: {e}")
            return None
        finally:
            self._return_connection(conn)
    
    def get_themes_by_analysis_run(self, analysis_run_id: int) -> List[Dict]:
        """
        Get themes for an analysis run
        
        Args:
            analysis_run_id: ID of the analysis run
            
        Returns:
            List of theme dictionaries
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                query = """
                    SELECT * FROM themes 
                    WHERE analysis_run_id = %s 
                    ORDER BY cluster_size DESC
                """
                cursor.execute(query, (analysis_run_id,))
                results = cursor.fetchall()
                
                return [dict(result) for result in results]
                
        except Exception as e:
            logger.error(f"Failed to get themes: {e}")
            return []
        finally:
            self._return_connection(conn)
    
    def get_latest_analysis_run(self, product_id: int) -> Optional[Dict]:
        """
        Get latest analysis run for a product
        
        Args:
            product_id: ID of the product
            
        Returns:
            Latest analysis run dictionary or None
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                query = """
                    SELECT * FROM analysis_runs 
                    WHERE product_id = %s 
                    ORDER BY analysis_timestamp DESC 
                    LIMIT 1
                """
                cursor.execute(query, (product_id,))
                result = cursor.fetchone()
                
                if result:
                    return dict(result)
                return None
                
        except Exception as e:
            logger.error(f"Failed to get latest analysis run: {e}")
            return None
        finally:
            self._return_connection(conn)
    
    def close(self):
        """Close database connection pool"""
        if self.pool:
            self.pool.closeall()
            logger.info("Database connection pool closed")


# Factory function
def create_phase3_database(config: dict) -> Phase3Database:
    """Create Phase3Database instance"""
    return Phase3Database(config)
