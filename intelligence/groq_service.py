"""
Groq LLM Service - Token-Optimized Emergency Analysis

This module provides LLM-powered emergency analysis using Groq's
ultra-fast LLaMA 70B inference. Designed for minimal token usage.
"""

import os
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import groq, handle if not installed
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    logger.warning("Groq package not installed. LLM features disabled.")


# Token-optimized system prompt (~80 tokens)
SYSTEM_PROMPT = """You are an emergency response analyst. Analyze the emergency message and respond ONLY with valid JSON:
{"emergency_type":"medical|safety|accident|emotional|unknown","urgency":1-100,"panic_level":1-10,"emotional_state":"calm|anxious|panicked|distressed|fearful","skills":["skill1","skill2"],"reasoning":"brief explanation"}"""

# Valid categories for validation
VALID_TYPES = {'medical', 'safety', 'accident', 'emotional', 'unknown'}
VALID_EMOTIONS = {'calm', 'anxious', 'panicked', 'distressed', 'fearful', 'unknown'}


class GroqAnalyzer:
    """Token-optimized Groq LLM analyzer for emergency classification."""
    
    def __init__(self):
        self.client = None
        self.enabled = False
        self._initialize()
    
    def _initialize(self):
        """Initialize Groq client if available and configured."""
        if not GROQ_AVAILABLE:
            logger.info("Groq not available - using rule-based analysis only")
            return
        
        api_key = os.getenv('GROQ_API_KEY', '')
        if not api_key:
            logger.info("GROQ_API_KEY not set - using rule-based analysis only")
            return
        
        try:
            self.client = Groq(api_key=api_key)
            self.enabled = True
            logger.info("Groq LLM analyzer initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Groq: {e}")
    
    def should_use_llm(self, description: str, has_card: bool = False) -> bool:
        """
        Determine if LLM analysis should be used (token optimization).
        
        Skip LLM when:
        - LLM not enabled
        - Description is empty or very short
        - Emergency card already selected (has keywords)
        """
        if not self.enabled:
            return False
        
        if not description or len(description.strip()) < 5:
            return False
        
        # If card is selected, card keywords are often sufficient
        if has_card:
            return False
        
        return True
    
    def analyze(self, description: str, context: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """
        Analyze emergency text using Groq LLaMA 70B.
        
        Token optimizations:
        - Truncate input to 500 chars
        - Compact system prompt
        - max_tokens=200
        - JSON-only response
        
        Args:
            description: Emergency description text
            context: Optional additional context (silent_mode, etc.)
        
        Returns:
            Analysis dict or None if failed
        """
        if not self.enabled:
            return None
        
        # Token optimization: truncate long descriptions
        truncated = description[:500] if len(description) > 500 else description
        
        # Build user message with context
        user_msg = truncated
        if context:
            if context.get('silent_mode'):
                user_msg += " [SILENT MODE - user cannot speak]"
            if context.get('is_bystander'):
                user_msg += " [BYSTANDER REPORT]"
        
        try:
            response = self.client.chat.completions.create(
                model=os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile'),
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg}
                ],
                max_tokens=int(os.getenv('GROQ_MAX_TOKENS', 200)),
                temperature=0.3,  # Low temp for consistent output
                response_format={"type": "json_object"}
            )
            
            # Parse response
            content = response.choices[0].message.content
            result = json.loads(content)
            
            # Validate and normalize response
            return self._validate_response(result)
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM JSON response: {e}")
            return None
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return None
    
    def _validate_response(self, result: Dict) -> Dict[str, Any]:
        """Validate and normalize LLM response."""
        validated = {
            'emergency_type': result.get('emergency_type', 'unknown'),
            'urgency_score': max(0, min(100, int(result.get('urgency', 50)))),
            'panic_level': max(1, min(10, int(result.get('panic_level', 5)))),
            'emotional_state': result.get('emotional_state', 'unknown'),
            'recommended_skills': result.get('skills', []),
            'llm_reasoning': result.get('reasoning', ''),
            'analysis_method': 'llm'
        }
        
        # Ensure valid types
        if validated['emergency_type'] not in VALID_TYPES:
            validated['emergency_type'] = 'unknown'
        
        if validated['emotional_state'] not in VALID_EMOTIONS:
            validated['emotional_state'] = 'unknown'
        
        return validated


# Singleton instance
_analyzer: Optional[GroqAnalyzer] = None


def get_analyzer() -> GroqAnalyzer:
    """Get or create the Groq analyzer singleton."""
    global _analyzer
    if _analyzer is None:
        _analyzer = GroqAnalyzer()
    return _analyzer


def analyze_with_llm(
    description: str,
    context: Optional[Dict] = None,
    has_card: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Convenience function for LLM analysis.
    
    Args:
        description: Emergency text
        context: Optional context dict
        has_card: Whether emergency card is selected
    
    Returns:
        LLM analysis result or None if should skip/failed
    """
    analyzer = get_analyzer()
    
    if not analyzer.should_use_llm(description, has_card):
        return None
    
    return analyzer.analyze(description, context)
