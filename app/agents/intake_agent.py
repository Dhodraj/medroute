import re
from typing import Optional
from loguru import logger

from . import Agent
from ..schemas import AgentInput, AgentOutput, TriageLevel


class IntakeAgent:
    """Agent responsible for input validation and cleaning"""
    
    def __init__(self):
        self.max_length = 2000
        self.min_length = 5
        
    def process(self, input_data: AgentInput) -> AgentOutput:
        """Clean and validate the input query"""
        try:
            query = input_data.query.strip()
            
            # Basic validation
            if len(query) < self.min_length:
                raise ValueError(f"Query too short (minimum {self.min_length} characters)")
            
            if len(query) > self.max_length:
                query = query[:self.max_length]
                logger.warning(f"Query truncated to {self.max_length} characters")
            
            # Language detection (basic English check)
            if not self._is_likely_english(query):
                raise ValueError("Non-English text detected. English-only supported.")
            
            # Clean the query
            cleaned_query = self._clean_text(query)
            
            # Update metadata
            metadata = input_data.metadata.copy()
            metadata.update({
                "intake_agent": {
                    "original_length": len(input_data.query),
                    "cleaned_length": len(cleaned_query),
                    "language_check": "passed"
                }
            })
            
            return AgentOutput(
                query=cleaned_query,
                symptoms=input_data.symptoms,
                triage_level=input_data.triage_level,
                recommendation=input_data.recommendation,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"IntakeAgent error: {e}")
            raise ValueError(f"Input validation failed: {e}")
    
    def _is_likely_english(self, text: str) -> bool:
        """Basic check if text is likely English"""
        # Simple heuristic: check for common English words and character patterns
        english_indicators = ['the', 'and', 'a', 'an', 'is', 'was', 'have', 'has', 'pain', 'hurt', 'feel']
        text_lower = text.lower()
        
        # Check for English indicators
        indicator_count = sum(1 for word in english_indicators if word in text_lower)
        
        # Check for non-ASCII characters (rough approximation)
        ascii_ratio = sum(1 for char in text if ord(char) < 128) / len(text)
        
        return indicator_count > 0 and ascii_ratio > 0.8
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize the input text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters that might interfere with processing
        text = re.sub(r'[^\w\s\.,;:!?\-\(\)]', ' ', text)
        
        # Normalize punctuation spacing
        text = re.sub(r'\s*([,.;:!?])\s*', r'\1 ', text)
        
        return text.strip()
