import re
import json
from typing import List, Dict, Any, Optional
from loguru import logger

from . import Agent
from ..schemas import AgentInput, AgentOutput, Symptom
from ..models.model_factory import get_model


class SymptomExtractionAgent:
    """Agent responsible for extracting structured symptoms from text"""
    
    def __init__(self):
        self.model = get_model()
        
        # Common symptom patterns for regex fallback
        self.symptom_patterns = [
            # Pain patterns
            (r'(\w+\s+)?pain(?:\s+in\s+(?:my\s+)?(\w+))?', 'pain'),
            (r'(\w+\s+)?ache(?:\s+in\s+(?:my\s+)?(\w+))?', 'ache'),
            (r'(\w+\s+)?hurt(?:s)?(?:\s+in\s+(?:my\s+)?(\w+))?', 'hurt'),
            
            # Duration patterns
            (r'for\s+(\d+)\s+(hour|minute|day|week|month)s?', 'duration'),
            (r'since\s+(yesterday|morning|evening|\d+)', 'duration'),
            (r'(\d+)\s+(hour|minute|day|week|month)s?\s+ago', 'duration'),
            
            # Severity patterns
            (r'(severe|mild|moderate|intense|sharp|dull|throbbing)', 'severity'),
            
            # Common symptoms
            (r'(fever|nausea|vomiting|dizziness|headache|fatigue|cough|shortness of breath)', 'symptom'),
        ]
    
    def process(self, input_data: AgentInput) -> AgentOutput:
        """Extract symptoms using LLM and regex fallback"""
        try:
            # Try LLM extraction first
            symptoms = self._extract_with_llm(input_data.query)
            
            # Fallback to regex if LLM fails or returns empty
            if not symptoms:
                logger.warning("LLM symptom extraction failed, using regex fallback")
                symptoms = self._extract_with_regex(input_data.query)
            
            # Merge with existing symptoms
            all_symptoms = input_data.symptoms + symptoms
            
            # Deduplicate symptoms
            unique_symptoms = self._deduplicate_symptoms(all_symptoms)
            
            # Update metadata
            metadata = input_data.metadata.copy()
            metadata.update({
                "symptom_extraction": {
                    "method": "llm" if symptoms else "regex",
                    "extracted_count": len(symptoms),
                    "total_count": len(unique_symptoms)
                }
            })
            
            return AgentOutput(
                query=input_data.query,
                symptoms=unique_symptoms,
                triage_level=input_data.triage_level,
                recommendation=input_data.recommendation,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"SymptomExtractionAgent error: {e}")
            # Return original input with empty symptoms on error
            return AgentOutput(
                query=input_data.query,
                symptoms=input_data.symptoms,
                triage_level=input_data.triage_level,
                recommendation=input_data.recommendation,
                metadata=input_data.metadata
            )
    
    def _extract_with_llm(self, query: str) -> List[Symptom]:
        """Extract symptoms using LLM"""
        try:
            prompt = f"""
Extract symptoms from the following medical complaint. Return ONLY a JSON list of symptoms with the following format:
[
    {{
        "name": "symptom name",
        "duration": "duration if mentioned",
        "severity": "mild/moderate/severe/unknown",
        "location": "body location if specified",
        "additional_info": "any other relevant details"
    }}
]

Medical complaint: "{query}"

Response (JSON only):"""
            
            response = self.model.generate_response(prompt, max_tokens=300, temperature=0.3)
            
            # Try to parse JSON response
            try:
                symptom_data = json.loads(response)
                return [Symptom(**symptom) for symptom in symptom_data if isinstance(symptom, dict)]
            except json.JSONDecodeError:
                # Try to extract JSON from response
                json_match = re.search(r'\[.*\]', response, re.DOTALL)
                if json_match:
                    symptom_data = json.loads(json_match.group())
                    return [Symptom(**symptom) for symptom in symptom_data if isinstance(symptom, dict)]
                
            return []
            
        except Exception as e:
            logger.warning(f"LLM symptom extraction failed: {e}")
            return []
    
    def _extract_with_regex(self, query: str) -> List[Symptom]:
        """Extract symptoms using regex patterns"""
        symptoms = []
        query_lower = query.lower()
        
        # Extract main symptoms
        for pattern, symptom_type in self.symptom_patterns:
            matches = re.finditer(pattern, query_lower)
            for match in matches:
                if symptom_type in ['symptom', 'pain', 'ache', 'hurt']:
                    symptom_name = match.group(0)
                    location = match.group(2) if len(match.groups()) > 1 and match.group(2) else None
                    
                    symptoms.append(Symptom(
                        name=symptom_name,
                        location=location,
                        severity="unknown"
                    ))
        
        # If no specific symptoms found, create a generic one
        if not symptoms:
            symptoms.append(Symptom(
                name="general complaint",
                severity="unknown",
                additional_info=query[:100] + "..." if len(query) > 100 else query
            ))
        
        return symptoms
    
    def _deduplicate_symptoms(self, symptoms: List[Symptom]) -> List[Symptom]:
        """Remove duplicate symptoms based on name similarity"""
        if not symptoms:
            return []
        
        unique_symptoms = []
        seen_names = set()
        
        for symptom in symptoms:
            name_key = symptom.name.lower().strip()
            if name_key not in seen_names:
                unique_symptoms.append(symptom)
                seen_names.add(name_key)
        
        return unique_symptoms
