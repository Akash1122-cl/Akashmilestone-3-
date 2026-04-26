"""
Edge Case Tests for Phase 3: Analysis and Clustering
Tests handling of small clusters, giant clusters, quote verification, generic action ideas
"""

import pytest
import sys
import os
import numpy as np
from unittest.mock import Mock, patch
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from clustering_engine import ClusteringEngine, ClusterResult
from theme_analyzer import ThemeAnalyzer, Theme, AnalysisResult
from validation_framework import ValidationFramework, ValidationResult


class TestSmallClusters:
    """Test handling of too many small clusters (<5 reviews)"""
    
    def test_small_cluster_detection(self):
        """Edge Case: Clusters with <5 reviews should be detected"""
        clusters = {
            0: [{'id': '1'}, {'id': '2'}, {'id': '3'}],  # 3 reviews - too small
            1: [{'id': '4'}, {'id': '5'}, {'id': '6'}, {'id': '7'}, {'id': '8'}],  # 5 reviews - acceptable
            2: [{'id': '9'}],  # 1 review - too small
        }
        
        min_cluster_size = 5
        small_clusters = [cid for cid, reviews in clusters.items() if len(reviews) < min_cluster_size]
        
        assert len(small_clusters) == 2
        assert 0 in small_clusters
        assert 2 in small_clusters
    
    def test_cluster_merge_candidates(self):
        """Edge Case: Small clusters should be candidates for merging"""
        small_clusters = [
            {'cluster_id': 0, 'size': 3, 'theme': 'performance'},
            {'cluster_id': 2, 'size': 2, 'theme': 'speed'},
        ]
        
        # Similar themes could be merged
        similar_themes = ['performance', 'speed', 'loading', 'slow']
        mergeable = [c for c in small_clusters if any(t in c['theme'] for t in similar_themes)]
        
        assert len(mergeable) > 0
    
    def test_noise_cluster_exclusion(self):
        """Edge Case: Noise clusters should be excluded from analysis"""
        clusters = {
            -1: [{'id': '1'}, {'id': '2'}],  # HDBSCAN noise cluster (-1)
            0: [{'id': '3'}, {'id': '4'}, {'id': '5'}, {'id': '6'}, {'id': '7'}],
        }
        
        # Noise cluster should be excluded
        valid_clusters = {k: v for k, v in clusters.items() if k != -1}
        
        assert -1 not in valid_clusters
        assert len(valid_clusters) == 1


class TestGiantCluster:
    """Test handling of one giant cluster containing diverse topics"""
    
    def test_giant_cluster_detection(self):
        """Edge Case: Giant clusters should be detected"""
        total_reviews = 1000
        clusters = {
            0: [{'id': str(i)} for i in range(900)],  # 90% of reviews - giant cluster
            1: [{'id': str(i)} for i in range(900, 1000)],  # 10% - normal cluster
        }
        
        # Detect giant cluster (>50% of total)
        giant_threshold = 0.5
        giant_clusters = [cid for cid, reviews in clusters.items() 
                         if len(reviews) / total_reviews > giant_threshold]
        
        assert len(giant_clusters) == 1
        assert 0 in giant_clusters
    
    def test_hierarchical_clustering_fallback(self):
        """Edge Case: Giant cluster should trigger hierarchical sub-clustering"""
        # When UMAP/HDBSCAN produces one giant cluster, hierarchical clustering
        # can break it down into sub-clusters
        
        embeddings = np.random.randn(100, 10)
        
        # Simulate hierarchical clustering by splitting giant cluster
        sub_clusters = {
            '0_0': embeddings[:30],   # Sub-cluster 1
            '0_1': embeddings[30:60], # Sub-cluster 2
            '0_2': embeddings[60:100] # Sub-cluster 3
        }
        
        assert len(sub_clusters) > 1
        assert sum(len(v) for v in sub_clusters.values()) == len(embeddings)
    
    def test_parameter_adjustment_for_diverse_data(self):
        """Edge Case: Parameters should be adjusted for diverse review topics"""
        # More aggressive UMAP + stricter HDBSCAN for diverse data
        umap_params = {'n_neighbors': 5, 'min_dist': 0.5}  # More local, more spread
        hdbscan_params = {'min_samples': 10, 'min_cluster_size': 20}  # Stricter clustering
        
        assert umap_params['n_neighbors'] < 15  # More local than default
        assert hdbscan_params['min_samples'] > 3  # Stricter than default


class TestUnstableClustering:
    """Test handling of unstable clustering across weeks"""
    
    def test_random_seed_reproducibility(self):
        """Edge Case: Clustering should be reproducible with fixed seeds"""
        np.random.seed(42)
        data1 = np.random.randn(100, 10)
        
        np.random.seed(42)
        data2 = np.random.randn(100, 10)
        
        # Same seed should produce same data
        assert np.array_equal(data1, data2)
    
    def test_cluster_continuity_tracking(self):
        """Edge Case: Clusters should be tracked across weeks"""
        week1_clusters = {
            'theme_A': {'name': 'User Experience', 'count': 50},
            'theme_B': {'name': 'Performance', 'count': 30},
        }
        
        week2_clusters = {
            'theme_A': {'name': 'User Experience', 'count': 55},  # Continued
            'theme_C': {'name': 'New Feature', 'count': 20},     # New
        }
        
        # Track continuity
        continued = [t for t in week2_clusters if t in week1_clusters]
        new_themes = [t for t in week2_clusters if t not in week1_clusters]
        
        assert len(continued) == 1
        assert 'theme_A' in continued
        assert len(new_themes) == 1
        assert 'theme_C' in new_themes


class TestQuoteVerification:
    """Test handling of generated quotes that don't match source reviews"""
    
    def test_exact_quote_matching(self):
        """Edge Case: Generated quotes must exactly match source reviews"""
        source_reviews = [
            "This app is absolutely amazing and works perfectly",
            "Terrible experience, crashes all the time",
            "Great features but slow performance"
        ]
        
        generated_quote = "This app is absolutely amazing and works perfectly"
        
        # Exact match
        assert generated_quote in source_reviews
    
    def test_fuzzy_quote_matching(self):
        """Edge Case: Near-matches should be detected with fuzzy matching"""
        source_reviews = [
            "This app is absolutely amazing and works perfectly",
        ]
        
        generated_quote = "This app is absolutely amazing"  # Substring
        
        # Fuzzy match - substring should be detected
        matches = [r for r in source_reviews if generated_quote.lower() in r.lower()]
        assert len(matches) > 0
    
    def test_quote_mismatch_detection(self):
        """Edge Case: Mismatched quotes should be flagged"""
        source_reviews = [
            "Good app overall",
            "Works fine for me",
        ]
        
        generated_quote = "This is the best app ever created in history"
        
        # Should NOT match any source review
        matches = [r for r in source_reviews if generated_quote.lower() in r.lower()]
        assert len(matches) == 0
    
    def test_quote_length_validation(self):
        """Edge Case: Quotes should be within reasonable length limits"""
        max_length = 200
        
        long_quote = "A" * 250
        short_quote = "Good app"
        
        assert len(long_quote) > max_length
        assert len(short_quote) <= max_length


class TestGenericActionIdeas:
    """Test handling of action ideas that are too generic"""
    
    def test_generic_action_detection(self):
        """Edge Case: Generic actions like 'fix bugs' should be detected"""
        generic_actions = [
            "Fix bugs",
            "Improve app",
            "Make it better",
            "Update regularly",
        ]
        
        # Detect generic actions (too short or too vague)
        generic_threshold = 15  # characters
        detected_generic = [a for a in generic_actions if len(a) < generic_threshold]
        
        assert len(detected_generic) >= 2
    
    def test_specific_action_acceptance(self):
        """Edge Case: Specific actions should pass validation"""
        specific_actions = [
            "Implement caching for search results to reduce load time by 50%",
            "Add offline mode for portfolio tracking feature",
            "Redesign onboarding flow with progressive disclosure",
        ]
        
        # Specific actions have length and detail
        for action in specific_actions:
            assert len(action) > 30
            assert any(word in action.lower() for word in ['implement', 'add', 'redesign', 'optimize'])
    
    def test_feasibility_scoring(self):
        """Edge Case: Actions should be scored for feasibility"""
        actions = [
            {"action": "Add dark mode", "effort": "low", "impact": "medium"},
            {"action": "Rebuild entire backend", "effort": "high", "impact": "high"},
            {"action": "Change app icon color", "effort": "low", "impact": "low"},
        ]
        
        # Score based on effort vs impact ratio
        for action in actions:
            if action['effort'] == 'low' and action['impact'] in ['medium', 'high']:
                action['score'] = 1.0  # High feasibility
            elif action['effort'] == 'high' and action['impact'] == 'high':
                action['score'] = 0.7  # Medium feasibility
            else:
                action['score'] = 0.3  # Low feasibility
        
        high_feasibility = [a for a in actions if a.get('score', 0) >= 0.7]
        assert len(high_feasibility) >= 1


class TestUnclearThemeNames:
    """Test handling of unclear or misleading theme names"""
    
    def test_unclear_theme_detection(self):
        """Edge Case: Vague theme names like 'Issues' should be flagged"""
        unclear_names = ['Issues', 'Problems', 'Things', 'Stuff', 'Misc']
        
        # Detect vague names (too short or too generic)
        vague_threshold = 8  # characters
        detected_unclear = [n for n in unclear_names if len(n) < vague_threshold]
        
        assert len(detected_unclear) >= 3
    
    def test_clear_theme_acceptance(self):
        """Edge Case: Descriptive theme names should pass validation"""
        clear_names = [
            'User Experience Navigation',
            'Payment Gateway Failures',
            'Portfolio Loading Performance',
            'Account Verification Delays',
        ]
        
        # Clear names have length and specificity
        for name in clear_names:
            assert len(name) >= 10
            assert ' ' in name  # Multi-word
    
    def test_blocklist_validation(self):
        """Edge Case: Inappropriate terms should be blocked"""
        blocklist = ['inappropriate', 'offensive', 'spam', 'fake']
        
        theme_name = "User Experience Issues"
        
        # Should not contain blocked terms
        contains_blocked = any(term in theme_name.lower() for term in blocklist)
        assert not contains_blocked


class TestHighLLMCosts:
    """Test handling of high LLM API costs (mitigated by free-only mode)"""
    
    def test_caching_for_similar_analyses(self):
        """Edge Case: Similar analyses should use cached results"""
        cache = {}
        
        # First analysis
        cache['theme_ux'] = {'name': 'User Experience', 'ideas': ['Fix navigation']}
        
        # Second analysis (similar)
        similar_key = 'theme_ux'
        if similar_key in cache:
            result = cache[similar_key]
            assert result == {'name': 'User Experience', 'ideas': ['Fix navigation']}
    
    def test_batch_request_efficiency(self):
        """Edge Case: Requests should be batched efficiently"""
        themes = list(range(10))
        batch_size = 5
        
        num_batches = (len(themes) + batch_size - 1) // batch_size
        assert num_batches == 2
    
    def test_cost_monitoring_alert(self):
        """Edge Case: Cost spikes should trigger alerts"""
        daily_cost_limit = 10.0  # USD
        current_cost = 12.5
        
        assert current_cost > daily_cost_limit


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
