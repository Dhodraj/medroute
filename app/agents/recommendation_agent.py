from typing import List, Dict, Any
from loguru import logger

from . import Agent
from ..schemas import AgentInput, AgentOutput, TriageLevel, Symptom
from ..models.model_factory import get_model


class RecommendationAgent:
    """Agent responsible for generating recommendations and disclaimers"""
    
    def __init__(self):
        self.model = get_model()
        self.disclaimer = "This is not a medical diagnosis. Consult a licensed doctor."
        
        # Template recommendations for rule-based fallback
        self.recommendation_templates = {
            TriageLevel.EMERGENCY: [
                "Seek emergency medical care immediately.",
                "Call 911 or go to the nearest emergency room right away.",
                "This requires immediate medical attention."
            ],
            TriageLevel.URGENT: [
                "Seek medical care within the next few hours.",
                "Contact your doctor or visit an urgent care center today.",
                "This condition needs prompt medical attention."
            ],
            TriageLevel.SEMI_URGENT: [
                "Schedule an appointment with your doctor within 24-48 hours.",
                "Monitor symptoms and seek care if they worsen.",
                "Consider visiting a clinic or scheduling a doctor's appointment soon."
            ],
            TriageLevel.NON_URGENT: [
                "Schedule a routine appointment with your healthcare provider.",
                "Monitor symptoms and seek care if they persist or worsen.",
                "Consider discussing this with your doctor at your next visit."
            ]
        }
    
    def process(self, input_data: AgentInput) -> AgentOutput:
        """Generate appropriate recommendations based on triage level"""
        try:
            # Generate LLM-based recommendation
            llm_recommendation = self._generate_llm_recommendation(
                input_data.query, 
                input_data.symptoms, 
                input_data.triage_level
            )
            
            # Use LLM recommendation if available, otherwise use template
            if llm_recommendation:
                recommendation = llm_recommendation
                method = "llm"
            else:
                recommendation = self._generate_template_recommendation(input_data.triage_level)
                method = "template"
            
            # Add disclaimer
            full_recommendation = f"{recommendation} {self.disclaimer}"
            
            # Update metadata
            metadata = input_data.metadata.copy()
            metadata.update({
                "recommendation_agent": {
                    "method": method,
                    "triage_level": input_data.triage_level.value if input_data.triage_level else None
                }
            })
            
            return AgentOutput(
                query=input_data.query,
                symptoms=input_data.symptoms,
                triage_level=input_data.triage_level,
                recommendation=full_recommendation,
                confidence_score=input_data.confidence_score,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"RecommendationAgent error: {e}")
            
            # Fallback to safe emergency recommendation
            return AgentOutput(
                query=input_data.query,
                symptoms=input_data.symptoms,
                triage_level=input_data.triage_level,
                recommendation=f"Seek medical care for your symptoms. {self.disclaimer}",
                confidence_score=input_data.confidence_score,
                metadata=input_data.metadata
            )
    
    def _generate_llm_recommendation(self, query: str, symptoms: List[Symptom], triage_level: TriageLevel) -> str:
        """Generate recommendation using LLM"""
        try:
            # Prepare symptoms summary
            symptoms_text = ""
            if symptoms:
                symptoms_list = [symptom.name for symptom in symptoms]
                symptoms_text = f"Symptoms: {', '.join(symptoms_list[:3])}"  # Limit to 3 symptoms
            
            urgency_context = {
                TriageLevel.EMERGENCY: "immediate emergency medical care",
                TriageLevel.URGENT: "prompt medical care within hours",
                TriageLevel.SEMI_URGENT: "medical care within 24-48 hours",
                TriageLevel.NON_URGENT: "routine medical care when convenient"
            }
            
            # Get triage level value safely - handle both enum and string
            if isinstance(triage_level, TriageLevel):
                triage_level_str = triage_level.value
                context_key = triage_level
            elif isinstance(triage_level, str):
                triage_level_str = triage_level
                # Try to convert string to enum for context lookup
                try:
                    context_key = TriageLevel(triage_level)
                except ValueError:
                    context_key = TriageLevel.NON_URGENT  # fallback
            else:
                triage_level_str = str(triage_level)
                context_key = TriageLevel.NON_URGENT  # fallback
            
            prompt = f"""
Generate a brief, clear medical recommendation (1-2 sentences) for a patient with the following:

Patient complaint: "{query}"
{symptoms_text}
Triage level: {triage_level_str}

The recommendation should suggest {urgency_context.get(context_key, 'medical care')} and be helpful but not diagnostic.

Keep it under 50 words. Do not include disclaimers.

Recommendation:"""
            
            response = self.model.generate_response(prompt, max_tokens=80, temperature=0.3)
            
            # Clean up the response
            recommendation = response.strip()
            
            # Basic validation
            if len(recommendation) > 200 or len(recommendation) < 10:
                return ""
            
            # Remove any disclaimers that might have been added
            disclaimer_phrases = [
                "this is not a medical diagnosis",
                "consult a doctor",
                "seek medical advice",
                "disclaimer"
            ]
            
            for phrase in disclaimer_phrases:
                recommendation = recommendation.replace(phrase, "").strip()
            
            return recommendation
            
        except Exception as e:
            logger.warning(f"LLM recommendation generation failed: {e}")
            return ""
    
    def _generate_template_recommendation(self, triage_level: TriageLevel) -> str:
        """Generate recommendation using templates"""
        templates = self.recommendation_templates.get(triage_level, self.recommendation_templates[TriageLevel.URGENT])
        return templates[0]  # Use first template for consistency
