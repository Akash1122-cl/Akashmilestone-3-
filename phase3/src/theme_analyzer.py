"""
Theme Analyzer for Phase 3
Implements LLM integration for theme naming, description generation, and action idea generation
"""

import logging
import json
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import time

# Try to import OpenAI
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI library not available, using mock theme analyzer")

logger = logging.getLogger(__name__)


@dataclass
class Theme:
    """Represents a discovered theme"""
    theme_id: str
    name: str
    description: str
    cluster_id: int
    cluster_size: int
    representative_quotes: List[str]
    action_ideas: List[str]
    sentiment_score: float
    quality_score: float
    metadata: Dict[str, Any]


@dataclass
class AnalysisResult:
    """Result from theme analysis operation"""
    product_id: int
    product_name: str
    themes: List[Theme]
    total_reviews: int
    analysis_timestamp: str
    processing_time_seconds: float
    metadata: Dict[str, Any]


class ThemeAnalyzer:
    """Theme analyzer using GPT-4 for theme naming and insights"""
    
    def __init__(self, config: dict):
        self.config = config.get('theme_analyzer', {})
        self.use_llm = self.config.get('use_llm', False)  # Free-only: default false
        self.llm_config = self.config.get('llm', {})
        self.theme_config = self.config.get('theme_generation', {})
        self.prompt_config = self.config.get('prompts', {})
        
        # Initialize OpenAI client
        self.client = None
        self.mock_mode = False
        
        # Free-only mode: skip API initialization entirely
        if not self.use_llm:
            logger.info("Free-only mode: Using template-based theme analyzer (no LLM API)")
            self.mock_mode = True
        elif not OPENAI_AVAILABLE:
            logger.info("OpenAI library not available, using mock theme analyzer")
            self.mock_mode = True
        else:
            self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI client"""
        try:
            api_key = self.llm_config.get('api_key')
            if not api_key:
                logger.warning("OpenAI API key not configured, using mock mode")
                self.mock_mode = True
                return
            
            self.client = openai.OpenAI(api_key=api_key)
            logger.info("OpenAI client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            self.mock_mode = True
    
    def analyze_themes(self, clusters: Dict[int, List[Dict]], 
                      reviews: List[Dict]) -> AnalysisResult:
        """
        Analyze clusters to generate themes with names, descriptions, and action ideas
        
        Args:
            clusters: Dictionary mapping cluster_id to list of review data
            reviews: Full list of review data
            
        Returns:
            AnalysisResult with themes and metadata
        """
        start_time = time.time()
        
        try:
            logger.info(f"Analyzing {len(clusters)} clusters")
            
            themes = []
            total_reviews = len(reviews)
            
            for cluster_id, cluster_reviews in clusters.items():
                if cluster_id == -1:  # Skip noise points
                    continue
                
                theme = self._analyze_cluster(cluster_id, cluster_reviews)
                if theme:
                    themes.append(theme)
            
            # Sort themes by cluster size
            themes.sort(key=lambda t: t.cluster_size, reverse=True)
            
            # Limit to max themes
            max_themes = self.theme_config.get('max_themes', 7)
            themes = themes[:max_themes]
            
            processing_time = time.time() - start_time
            
            # Build analysis result
            product_id = reviews[0].get('product_id', 0) if reviews else 0
            product_name = reviews[0].get('product_name', 'Unknown') if reviews else 'Unknown'
            
            result = AnalysisResult(
                product_id=product_id,
                product_name=product_name,
                themes=themes,
                total_reviews=total_reviews,
                analysis_timestamp=datetime.utcnow().isoformat(),
                processing_time_seconds=processing_time,
                metadata={
                    'total_clusters': len(clusters),
                    'themes_generated': len(themes),
                    'mock_mode': self.mock_mode
                }
            )
            
            logger.info(f"Theme analysis completed in {processing_time:.2f}s, "
                       f"generated {len(themes)} themes")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to analyze themes: {e}")
            raise
    
    def _analyze_cluster(self, cluster_id: int, 
                        cluster_reviews: List[Dict]) -> Optional[Theme]:
        """
        Analyze a single cluster to generate theme information
        
        Args:
            cluster_id: ID of the cluster
            cluster_reviews: List of review data in the cluster
            
        Returns:
            Theme object or None if analysis fails
        """
        try:
            logger.info(f"Analyzing cluster {cluster_id} with {len(cluster_reviews)} reviews")
            
            # Extract review texts for analysis
            review_texts = [r.get('text', '') for r in cluster_reviews if r.get('text')]
            
            if not review_texts:
                logger.warning(f"No review texts found for cluster {cluster_id}")
                return None
            
            # Generate theme name and description
            theme_name, theme_description = self._generate_theme_name_description(
                review_texts, cluster_id
            )
            
            # Extract representative quotes
            quotes = self._extract_representative_quotes(
                cluster_reviews, max_quotes=self.theme_config.get('quotes_per_theme', 3)
            )
            
            # Generate action ideas
            action_ideas = self._generate_action_ideas(
                theme_name, theme_description, review_texts
            )
            
            # Calculate sentiment score
            sentiment_score = self._calculate_sentiment_score(cluster_reviews)
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(
                theme_name, theme_description, quotes, action_ideas
            )
            
            # Create theme
            theme = Theme(
                theme_id=f"theme_{cluster_id}",
                name=theme_name,
                description=theme_description,
                cluster_id=cluster_id,
                cluster_size=len(cluster_reviews),
                representative_quotes=quotes,
                action_ideas=action_ideas,
                sentiment_score=sentiment_score,
                quality_score=quality_score,
                metadata={
                    'analysis_timestamp': datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Generated theme: {theme_name} for cluster {cluster_id}")
            return theme
            
        except Exception as e:
            logger.error(f"Failed to analyze cluster {cluster_id}: {e}")
            return None
    
    def _generate_theme_name_description(self, review_texts: List[str], 
                                        cluster_id: int) -> tuple[str, str]:
        """Generate theme name and description using LLM"""
        if self.mock_mode:
            return self._generate_mock_theme_name_description(cluster_id)
        
        try:
            prompt = self.prompt_config.get('theme_naming', '').format(
                reviews='\n'.join(review_texts[:10])  # Limit to 10 reviews for context
            )
            
            response = self._call_llm(prompt, max_tokens=300)
            
            # Parse response
            lines = response.strip().split('\n')
            theme_name = lines[0] if lines else f"Theme {cluster_id}"
            theme_description = ' '.join(lines[1:]) if len(lines) > 1 else "No description available"
            
            return theme_name, theme_description
            
        except Exception as e:
            logger.error(f"Failed to generate theme name/description: {e}")
            return self._generate_mock_theme_name_description(cluster_id)
    
    def _generate_mock_theme_name_description(self, cluster_id: int) -> tuple[str, str]:
        """Generate mock theme name and description"""
        mock_themes = [
            ("User Experience Issues", "Customers are experiencing difficulties with app navigation and usability"),
            ("Performance Problems", "Users report slow loading times and app crashes"),
            ("Feature Requests", "Customers are requesting new features and improvements"),
            ("Payment Issues", "Users are having problems with payments and transactions"),
            ("Customer Support", "Feedback about customer service responsiveness and quality"),
            ("Security Concerns", "Users expressing concerns about data security and privacy"),
            ("General Satisfaction", "Positive feedback about overall app experience")
        ]
        
        theme_name, theme_description = mock_themes[cluster_id % len(mock_themes)]
        return theme_name, theme_description
    
    def _extract_representative_quotes(self, cluster_reviews: List[Dict], 
                                      max_quotes: int = 3) -> List[str]:
        """Extract representative quotes from cluster reviews"""
        try:
            # Sort by text length (prefer medium-length quotes)
            sorted_reviews = sorted(
                cluster_reviews,
                key=lambda r: len(r.get('text', ''))
            )
            
            # Take from middle of sorted list to avoid very short or very long quotes
            mid_idx = len(sorted_reviews) // 2
            selected_reviews = sorted_reviews[
                max(0, mid_idx - max_quotes // 2):
                min(len(sorted_reviews), mid_idx + max_quotes // 2)
            ]
            
            quotes = []
            for review in selected_reviews[:max_quotes]:
                text = review.get('text', '').strip()
                if text:
                    # Truncate if too long
                    if len(text) > 200:
                        text = text[:197] + "..."
                    quotes.append(text)
            
            return quotes
            
        except Exception as e:
            logger.error(f"Failed to extract representative quotes: {e}")
            return []
    
    def _generate_action_ideas(self, theme_name: str, theme_description: str, 
                              review_texts: List[str]) -> List[str]:
        """Generate actionable ideas based on theme"""
        if self.mock_mode:
            return self._generate_mock_action_ideas(theme_name)
        
        try:
            if not self.theme_config.get('require_action_ideas', True):
                return []
            
            prompt = self.prompt_config.get('action_ideas', '').format(
                theme_name=theme_name,
                theme_description=theme_description,
                reviews='\n'.join(review_texts[:5])
            )
            
            response = self._call_llm(prompt, max_tokens=400)
            
            # Parse response (expect numbered list)
            action_ideas = []
            for line in response.strip().split('\n'):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-')):
                    # Remove number/bullet and whitespace
                    idea = line.lstrip('0123456789.- ').strip()
                    if idea:
                        action_ideas.append(idea)
            
            return action_ideas[:3]  # Limit to 3 action ideas
            
        except Exception as e:
            logger.error(f"Failed to generate action ideas: {e}")
            return self._generate_mock_action_ideas(theme_name)
    
    def _generate_mock_action_ideas(self, theme_name: str) -> List[str]:
        """Generate mock action ideas"""
        return [
            f"Investigate {theme_name.lower()} issues reported by users",
            f"Prioritize fixes for {theme_name.lower()} in next sprint",
            f"Conduct user research to understand {theme_name.lower()} better"
        ]
    
    def _calculate_sentiment_score(self, cluster_reviews: List[Dict]) -> float:
        """Calculate average sentiment score for cluster"""
        try:
            sentiment_scores = [
                r.get('sentiment_score', 0.5) for r in cluster_reviews
                if r.get('sentiment_score') is not None
            ]
            
            if not sentiment_scores:
                return 0.5
            
            return sum(sentiment_scores) / len(sentiment_scores)
            
        except Exception as e:
            logger.error(f"Failed to calculate sentiment score: {e}")
            return 0.5
    
    def _calculate_quality_score(self, theme_name: str, theme_description: str,
                                 quotes: List[str], action_ideas: List[str]) -> float:
        """Calculate quality score for theme"""
        try:
            score = 0.0
            
            # Theme name quality (0-0.3)
            if len(theme_name) > 3 and len(theme_name) < 50:
                score += 0.3
            
            # Description quality (0-0.2)
            if len(theme_description) > 20:
                score += 0.2
            
            # Quotes quality (0-0.3)
            if len(quotes) >= 2:
                score += 0.3
            
            # Action ideas quality (0-0.2)
            if len(action_ideas) >= 2:
                score += 0.2
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"Failed to calculate quality score: {e}")
            return 0.5
    
    def _call_llm(self, prompt: str, max_tokens: int = 500) -> str:
        """Call LLM API with retry logic"""
        max_retries = self.llm_config.get('max_retries', 3)
        retry_delay = self.llm_config.get('retry_delay', 2)
        
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.llm_config.get('model', 'gpt-4'),
                    messages=[
                        {"role": "system", "content": "You are a helpful analyst that analyzes customer reviews."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.llm_config.get('temperature', 0.7),
                    max_tokens=max_tokens
                )
                
                return response.choices[0].message.content
                
            except Exception as e:
                logger.warning(f"LLM call attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    raise
        
        return ""


# Factory function
def create_theme_analyzer(config: dict) -> ThemeAnalyzer:
    """Create ThemeAnalyzer instance"""
    return ThemeAnalyzer(config)
