"""
Narrative Builder for Phase 4
Implements narrative generation using Jinja2 templates and LLM integration
"""

import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import os

try:
    from jinja2 import Environment, FileSystemLoader, Template
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False
    logging.warning("Jinja2 not available, using basic string formatting")

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI not available, using mock executive summary")

logger = logging.getLogger(__name__)


@dataclass
class NarrativeSection:
    """Represents a section of the narrative"""
    section_name: str
    content: str
    metadata: Dict[str, Any]


@dataclass
class NarrativeResult:
    """Result from narrative generation"""
    executive_summary: str
    themes: List[NarrativeSection]
    quotes: List[NarrativeSection]
    action_ideas: List[NarrativeSection]
    impact_analysis: str
    generation_timestamp: str
    processing_time_seconds: float
    metadata: Dict[str, Any]


class NarrativeBuilder:
    """Narrative builder using Jinja2 templates and LLM integration"""
    
    def __init__(self, config: dict):
        self.config = config.get('narrative_builder', {})
        self.use_llm = self.config.get('use_llm', False)  # Free-only: default false
        self.template_engine = self.config.get('template_engine', 'jinja2')
        self.template_directory = self.config.get('template_directory', './templates')
        self.max_themes = self.config.get('max_themes', 7)
        self.min_themes = self.config.get('min_themes', 5)
        self.max_quotes_per_theme = self.config.get('max_quotes_per_theme', 3)
        self.max_action_ideas = self.config.get('max_action_ideas', 3)
        self.llm_config = self.config.get('llm', {})
        self.prompt_config = self.config.get('prompts', {})
        
        # Initialize template engine
        self.jinja_env = None
        self.mock_mode = False
        
        if JINJA2_AVAILABLE:
            try:
                # Get absolute path to templates directory
                if not os.path.isabs(self.template_directory):
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    self.template_directory = os.path.join(current_dir, '..', self.template_directory)
                
                self.jinja_env = Environment(
                    loader=FileSystemLoader(self.template_directory),
                    autoescape=True
                )
                logger.info(f"Jinja2 environment initialized with template directory: {self.template_directory}")
            except Exception as e:
                logger.error(f"Failed to initialize Jinja2: {e}")
                self.mock_mode = True
        else:
            logger.info("Using mock narrative builder mode")
            self.mock_mode = True
        
        # Initialize OpenAI client - only if use_llm is enabled (not free-only mode)
        self.openai_client = None
        if self.use_llm and OPENAI_AVAILABLE and self.llm_config.get('api_key'):
            try:
                self.openai_client = openai.OpenAI(api_key=self.llm_config.get('api_key'))
                logger.info("OpenAI client initialized for executive summary generation")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
        elif not self.use_llm:
            logger.info("Free-only mode: Using template-based executive summaries (no LLM API)")
    
    def build_narrative(self, analysis_result: Dict, themes: List[Dict]) -> NarrativeResult:
        """
        Build complete narrative from analysis results and themes
        
        Args:
            analysis_result: Analysis result from Phase 3
            themes: List of themes with metadata
            
        Returns:
            NarrativeResult with complete narrative
        """
        import time
        start_time = time.time()
        
        try:
            logger.info(f"Building narrative for {len(themes)} themes")
            
            # Generate executive summary
            executive_summary = self._generate_executive_summary(analysis_result, themes)
            
            # Build theme narratives
            theme_narratives = self._build_theme_narratives(themes)
            
            # Build quote sections
            quote_sections = self._build_quote_sections(themes)
            
            # Build action idea sections
            action_idea_sections = self._build_action_idea_sections(themes)
            
            # Generate impact analysis
            impact_analysis = self._generate_impact_analysis(themes)
            
            processing_time = time.time() - start_time
            
            result = NarrativeResult(
                executive_summary=executive_summary,
                themes=theme_narratives,
                quotes=quote_sections,
                action_ideas=action_idea_sections,
                impact_analysis=impact_analysis,
                generation_timestamp=datetime.utcnow().isoformat(),
                processing_time_seconds=processing_time,
                metadata={
                    'total_themes': len(themes),
                    'mock_mode': self.mock_mode
                }
            )
            
            logger.info(f"Narrative built in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Failed to build narrative: {e}")
            raise
    
    def _generate_executive_summary(self, analysis_result: Dict, themes: List[Dict]) -> str:
        """Generate executive summary using LLM"""
        if self.mock_mode or not self.openai_client:
            return self._generate_mock_executive_summary(analysis_result, themes)
        
        try:
            # Prepare themes summary
            themes_summary = ", ".join([t.get('name', 'Unknown') for t in themes[:5]])
            
            prompt = self.prompt_config.get('executive_summary', '').format(
                product_name=analysis_result.get('product_name', 'Unknown'),
                total_reviews=analysis_result.get('total_reviews', 0),
                themes_summary=themes_summary
            )
            
            response = self._call_llm(prompt, max_tokens=300)
            return response.strip()
            
        except Exception as e:
            logger.error(f"Failed to generate executive summary: {e}")
            return self._generate_mock_executive_summary(analysis_result, themes)
    
    def _generate_mock_executive_summary(self, analysis_result: Dict, themes: List[Dict]) -> str:
        """Generate mock executive summary"""
        product_name = analysis_result.get('product_name', 'the product')
        total_reviews = analysis_result.get('total_reviews', 0)
        num_themes = len(themes)
        
        return (f"This week, {product_name} received {total_reviews} reviews. "
                f"Our analysis identified {num_themes} key themes including "
                f"{themes[0].get('name', 'user feedback') if themes else 'general feedback'}. "
                f"Overall sentiment indicates areas for improvement in user experience.")
    
    def _build_theme_narratives(self, themes: List[Dict]) -> List[NarrativeSection]:
        """Build narrative sections for each theme"""
        narratives = []
        
        # Select top themes by cluster size
        sorted_themes = sorted(themes, key=lambda t: t.get('cluster_size', 0), reverse=True)
        selected_themes = sorted_themes[:self.max_themes]
        
        for theme in selected_themes:
            content = f"**{theme.get('name', 'Unknown')}**\n"
            content += f"{theme.get('description', 'No description available.')}\n"
            content += f"Cluster Size: {theme.get('cluster_size', 0)} reviews\n"
            content += f"Sentiment Score: {theme.get('sentiment_score', 0.0):.2f}\n"
            
            narratives.append(NarrativeSection(
                section_name=theme.get('name', 'unknown'),
                content=content,
                metadata={
                    'theme_id': theme.get('theme_id'),
                    'cluster_size': theme.get('cluster_size'),
                    'sentiment_score': theme.get('sentiment_score')
                }
            ))
        
        return narratives
    
    def _build_quote_sections(self, themes: List[Dict]) -> List[NarrativeSection]:
        """Build quote sections for each theme"""
        quote_sections = []
        
        for theme in themes[:self.max_themes]:
            quotes = theme.get('representative_quotes', [])
            selected_quotes = quotes[:self.max_quotes_per_theme]
            
            if selected_quotes:
                content = f"**Quotes for {theme.get('name', 'Unknown')}:**\n"
                for i, quote in enumerate(selected_quotes, 1):
                    content += f"{i}. \"{quote}\"\n"
                
                quote_sections.append(NarrativeSection(
                    section_name=f"{theme.get('name', 'unknown')}_quotes",
                    content=content,
                    metadata={
                        'theme_id': theme.get('theme_id'),
                        'quote_count': len(selected_quotes)
                    }
                ))
        
        return quote_sections
    
    def _build_action_idea_sections(self, themes: List[Dict]) -> List[NarrativeSection]:
        """Build action idea sections for each theme"""
        action_sections = []
        
        for theme in themes[:self.max_themes]:
            action_ideas = theme.get('action_ideas', [])
            selected_actions = action_ideas[:self.max_action_ideas]
            
            if selected_actions:
                content = f"**Action Ideas for {theme.get('name', 'Unknown')}:**\n"
                for i, action in enumerate(selected_actions, 1):
                    content += f"{i}. {action}\n"
                
                action_sections.append(NarrativeSection(
                    section_name=f"{theme.get('name', 'unknown')}_actions",
                    content=content,
                    metadata={
                        'theme_id': theme.get('theme_id'),
                        'action_count': len(selected_actions)
                    }
                ))
        
        return action_sections
    
    def _generate_impact_analysis(self, themes: List[Dict]) -> str:
        """Generate impact analysis"""
        if not themes:
            return "No impact analysis available."
        
        total_reviews = sum(t.get('cluster_size', 0) for t in themes)
        avg_sentiment = sum(t.get('sentiment_score', 0.5) for t in themes) / len(themes) if themes else 0.5
        
        analysis = f"**Impact Analysis:**\n"
        analysis += f"Total analyzed reviews: {total_reviews}\n"
        analysis += f"Average sentiment: {avg_sentiment:.2f}\n"
        analysis += f"Key themes identified: {len(themes)}\n"
        
        if avg_sentiment < 0.4:
            analysis += "Overall sentiment indicates significant user concerns requiring immediate attention."
        elif avg_sentiment < 0.6:
            analysis += "Overall sentiment indicates mixed feedback with areas for improvement."
        else:
            analysis += "Overall sentiment is positive with minor areas for enhancement."
        
        return analysis
    
    def _call_llm(self, prompt: str, max_tokens: int = 500) -> str:
        """Call LLM API with retry logic"""
        max_retries = self.llm_config.get('max_retries', 3)
        retry_delay = self.llm_config.get('retry_delay', 2)
        
        for attempt in range(max_retries):
            try:
                response = self.openai_client.chat.completions.create(
                    model=self.llm_config.get('model', 'gpt-4'),
                    messages=[
                        {"role": "system", "content": "You are a helpful analyst that summarizes customer feedback."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.llm_config.get('temperature', 0.7),
                    max_tokens=max_tokens
                )
                
                return response.choices[0].message.content
                
            except Exception as e:
                logger.warning(f"LLM call attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(retry_delay)
                else:
                    raise
        
        return ""
    
    def render_template(self, template_name: str, context: Dict) -> str:
        """Render a Jinja2 template with context"""
        if not self.jinja_env:
            return str(context)
        
        try:
            template = self.jinja_env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {e}")
            return str(context)


# Factory function
def create_narrative_builder(config: dict) -> NarrativeBuilder:
    """Create NarrativeBuilder instance"""
    return NarrativeBuilder(config)
