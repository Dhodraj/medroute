import re
from typing import List, Dict, Tuple, Optional
from loguru import logger

from . import Agent
from ..schemas import AgentInput, AgentOutput, TriageLevel, Symptom
from ..models.model_factory import get_model


class TriageAgent:
    """Agent responsible for determining triage level using rules and LLM"""
    
    def __init__(self):
        self.model = get_model()
        
        # Rule-based red flags that trigger immediate emergency classification
        self.emergency_red_flags = [
            # Cardiovascular
            r'chest\s+pain',
            r'heart\s+attack',
            r'cardiac\s+arrest',
            r'severe\s+chest\s+pressure',
            r'chest\s+pressure',
            
            # Respiratory
            r'can\'?t\s+breathe',
            r'cannot\s+breathe',
            r'can\s*not\s+breathe',
            r'severe\s+shortness\s+of\s+breath',
            r'difficulty\s+breathing',
            r'choking',
            r'breathe',  # More general pattern
            
            # Neurological
            r'stroke',
            r'severe\s+headache',
            r'sudden\s+weakness',
            r'cannot\s+speak',
            r'confusion\s+and\s+fever',
            
            # Trauma
            r'severe\s+bleeding',
            r'unconscious',
            r'severe\s+trauma',
            r'major\s+injury',
            
            # Other critical
            r'allergic\s+reaction',
            r'anaphylaxis',
            r'severe\s+abdominal\s+pain',
            r'signs\s+of\s+shock',
            r'having\s+a\s+heart\s+attack',
            r'think.*heart\s+attack'
        ]
        
        # Urgent conditions
        self.urgent_indicators = [
            r'moderate\s+pain',
            r'fever\s+over\s+101',
            r'persistent\s+vomiting',
            r'severe\s+headache',
            r'difficulty\s+urinating',
            r'blood\s+in\s+urine',
            r'severe\s+diarrhea'
        ]
        
        # Semi-urgent conditions  
        self.semi_urgent_indicators = [
            r'mild\s+pain',
            r'low\s+grade\s+fever',
            r'minor\s+cut',
            r'small\s+cut',
            r'minor\s+bleeding',
            r'rash',
            r'cold\s+symptoms',
            r'sore\s+throat',
            r'mild\s+fever'
        ]
        
        # Non-urgent conditions
        self.non_urgent_indicators = [
            r'mild\s+headache',
            r'feeling\s+tired',
            r'routine\s+checkup',
            r'feeling\s+fine',
            r'checkup',
            r'tired'
        ]
    
    def process(self, input_data: AgentInput) -> AgentOutput:
        """Determine triage level using rule-based and LLM approaches"""
        try:
            # First, try LLM-based triage for full assessment
            llm_level, llm_confidence = self._apply_llm_triage(input_data.query, input_data.symptoms)
            
            # Also get rule-based assessment
            rule_based_level, rule_confidence = self._apply_rule_based_triage(input_data.query, input_data.symptoms)
            
            # Decision logic prioritizing LLM when available
            if llm_level and llm_confidence > 0.0:
                # LLM provided a valid response
                if rule_based_level == TriageLevel.EMERGENCY and llm_level != TriageLevel.EMERGENCY:
                    # Safety check: if rules suggest emergency but LLM doesn't, use emergency with combined confidence
                    triage_level = TriageLevel.EMERGENCY
                    final_confidence = max(llm_confidence, rule_confidence)
                    method = "safety_override"
                else:
                    # Use LLM result as primary
                    triage_level = llm_level
                    final_confidence = llm_confidence
                    method = "llm_primary"
            else:
                # Fall back to rule-based with LLM-enhanced confidence
                triage_level = rule_based_level
                final_confidence = rule_confidence
                method = "rule_based_with_llm_confidence"
            
            # Update metadata
            metadata = input_data.metadata.copy()
            metadata.update({
                "triage_agent": {
                    "method": method,
                    "llm_level": llm_level.value if llm_level else None,
                    "llm_confidence": llm_confidence,
                    "rule_based_level": rule_based_level.value if rule_based_level else None,
                    "rule_based_confidence": rule_confidence,
                    "final_confidence": final_confidence
                }
            })
            
            return AgentOutput(
                query=input_data.query,
                symptoms=input_data.symptoms,
                triage_level=triage_level,
                recommendation=input_data.recommendation,
                confidence_score=final_confidence,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"TriageAgent error: {e}")
            # Default to urgent as safe fallback
            return AgentOutput(
                query=input_data.query,
                symptoms=input_data.symptoms,
                triage_level=TriageLevel.URGENT,
                recommendation=input_data.recommendation,
                confidence_score=0.5,
                metadata=input_data.metadata
            )
    
    def _apply_rule_based_triage(self, query: str, symptoms: List[Symptom]) -> Tuple[Optional[TriageLevel], float]:
        """Apply rule-based triage logic with LLM confidence assessment"""
        query_lower = query.lower()
        suggested_level = None
        
        # Check for non-urgent conditions first (most specific)
        for pattern in self.non_urgent_indicators:
            if re.search(pattern, query_lower):
                suggested_level = TriageLevel.NON_URGENT
                break
        
        # Check for semi-urgent conditions
        if not suggested_level:
            for pattern in self.semi_urgent_indicators:
                if re.search(pattern, query_lower):
                    suggested_level = TriageLevel.SEMI_URGENT
                    break
        
        # Check for emergency red flags
        if not suggested_level:
            for pattern in self.emergency_red_flags:
                if re.search(pattern, query_lower):
                    suggested_level = TriageLevel.EMERGENCY
                    break
        
        # Check symptoms for emergency indicators
        if not suggested_level:
            for symptom in symptoms:
                symptom_text = f"{symptom.name} {symptom.additional_info or ''}".lower()
                for pattern in self.emergency_red_flags:
                    if re.search(pattern, symptom_text):
                        suggested_level = TriageLevel.EMERGENCY
                        break
                
                # Check severity
                if symptom.severity == "severe":
                    suggested_level = TriageLevel.EMERGENCY
                    break
                    
                if suggested_level:
                    break
        
        # Check for urgent conditions
        if not suggested_level:
            for pattern in self.urgent_indicators:
                if re.search(pattern, query_lower):
                    suggested_level = TriageLevel.URGENT
                    break
        
        # Default to non-urgent if no patterns match
        if not suggested_level:
            suggested_level = TriageLevel.NON_URGENT
        
        # Get LLM confidence for the suggested level
        try:
            llm_confidence = self._get_llm_confidence_for_level(query, symptoms, suggested_level)
            return suggested_level, llm_confidence
        except Exception as e:
            logger.warning(f"Failed to get LLM confidence, using fallback: {e}")
            # Fallback confidence scores based on rule type
            fallback_confidence = {
                TriageLevel.EMERGENCY: 0.85,
                TriageLevel.URGENT: 0.75,
                TriageLevel.SEMI_URGENT: 0.7,
                TriageLevel.NON_URGENT: 0.6
            }
            return suggested_level, fallback_confidence.get(suggested_level, 0.6)
    
    def _apply_llm_triage(self, query: str, symptoms: List[Symptom]) -> Tuple[Optional[TriageLevel], float]:
        """Apply LLM-based triage classification"""
        try:
            # Prepare symptoms summary
            symptoms_text = ""
            if symptoms:
                symptoms_list = []
                for symptom in symptoms:
                    symptom_desc = symptom.name
                    if symptom.severity:
                        symptom_desc += f" ({symptom.severity})"
                    if symptom.duration:
                        symptom_desc += f" for {symptom.duration}"
                    if symptom.location:
                        symptom_desc += f" in {symptom.location}"
                    symptoms_list.append(symptom_desc)
                symptoms_text = "Symptoms: " + ", ".join(symptoms_list)
            
            prompt = f"""
You are a medical AI assistant helping train a triage system. This is for educational and system development purposes only, not real patient care.

For this training scenario, classify the triage level and provide a confidence score:

Triage levels:
- emergency: Life-threatening, needs immediate care
- urgent: Serious but stable, needs care within hours  
- semi_urgent: Needs care within 24-48 hours
- non_urgent: Can wait days/weeks for routine care

Training scenario: "{query}"
{symptoms_text}

Guidelines for classification:
- Chest pain, difficulty breathing, stroke symptoms = emergency
- Severe pain, high fever, persistent vomiting = urgent
- Moderate symptoms, minor injuries = semi_urgent  
- Mild symptoms, routine concerns = non_urgent

For training purposes, provide your assessment in this exact format:
[triage_level]:[confidence_0_to_1]

Training examples:
- emergency:0.92
- urgent:0.78
- semi_urgent:0.65
- non_urgent:0.83

Your training assessment:"""
            
            response = self.model.generate_response(prompt, max_tokens=50, temperature=0.1)
            
            # Parse response - handle multiple formats
            # Format 1: emergency:0.9
            match = re.search(r'(emergency|urgent|semi_urgent|non_urgent):\s*([0-9.]+)', response.lower())
            if not match:
                # Format 2: [Triage Level 1]: [0.95] (medgemma format)
                level_match = re.search(r'\[triage\s+level\s+(\d+)\]', response.lower())
                conf_match = re.search(r'\[([0-9.]+)\]', response)
                if level_match and conf_match:
                    level_num = int(level_match.group(1))
                    confidence_str = conf_match.group(1)
                    try:
                        confidence = float(confidence_str)
                        confidence = max(0.0, min(1.0, confidence))
                        
                        # Map level numbers to triage levels (medical convention)
                        level_mapping = {
                            1: TriageLevel.EMERGENCY,      # Level 1 = Most urgent
                            2: TriageLevel.URGENT,         # Level 2 = Urgent
                            3: TriageLevel.SEMI_URGENT,    # Level 3 = Semi-urgent
                            4: TriageLevel.NON_URGENT,     # Level 4 = Non-urgent
                            5: TriageLevel.NON_URGENT      # Level 5 = Non-urgent
                        }
                        
                        if level_num in level_mapping:
                            return level_mapping[level_num], confidence
                    except ValueError:
                        pass
            else:
                # Handle standard format
                level_str, confidence_str = match.groups()
                try:
                    confidence = float(confidence_str)
                    # Ensure confidence is within valid range
                    confidence = max(0.0, min(1.0, confidence))
                    
                    if level_str == "emergency":
                        return TriageLevel.EMERGENCY, confidence
                    elif level_str == "urgent":
                        return TriageLevel.URGENT, confidence
                    elif level_str == "semi_urgent":
                        return TriageLevel.SEMI_URGENT, confidence
                    elif level_str == "non_urgent":
                        return TriageLevel.NON_URGENT, confidence
                except ValueError:
                    pass
            
            return None, 0.0
            
        except Exception as e:
            logger.warning(f"LLM triage failed: {e}")
            return None, 0.0
    
    def _get_llm_confidence_for_level(self, query: str, symptoms: List[Symptom], suggested_level: TriageLevel) -> float:
        """Get LLM confidence score for a suggested triage level"""
        try:
            # Prepare symptoms summary
            symptoms_text = ""
            if symptoms:
                symptoms_list = []
                for symptom in symptoms:
                    symptom_desc = symptom.name
                    if symptom.severity:
                        symptom_desc += f" ({symptom.severity})"
                    if symptom.duration:
                        symptom_desc += f" for {symptom.duration}"
                    if symptom.location:
                        symptom_desc += f" in {symptom.location}"
                    symptoms_list.append(symptom_desc)
                symptoms_text = "Symptoms: " + ", ".join(symptoms_list)
            
            prompt = f"""
You are a medical AI helping develop a triage training system. This is for educational and system validation purposes only.

A preliminary triage assessment suggests classifying this training case as "{suggested_level.value}".

Training scenario: "{query}"
{symptoms_text}

For this educational exercise, evaluate how confident you would be in this "{suggested_level.value}" classification.

Consider for training purposes:
- Clarity of symptoms described
- Amount of information available  
- Certainty of the classification
- Potential for misclassification

For this training scenario, provide only a confidence score between 0.0 and 1.0.

Training examples:
- Very clear emergency signs: 0.95
- Typical urgent case with good info: 0.85
- Limited info but likely correct: 0.65
- Uncertain classification: 0.45

Training confidence score:"""
            
            response = self.model.generate_response(prompt, max_tokens=10, temperature=0.1)
            
            # Parse confidence score - handle multiple formats
            # Format 1: 0.85
            match = re.search(r'([0-9.]+)', response.strip())
            if match:
                try:
                    confidence = float(match.group(1))
                    # Ensure confidence is within valid range
                    return max(0.0, min(1.0, confidence))
                except ValueError:
                    pass
            
            # Format 2: [0.85] (medgemma format)
            bracket_match = re.search(r'\[([0-9.]+)\]', response)
            if bracket_match:
                try:
                    confidence = float(bracket_match.group(1))
                    return max(0.0, min(1.0, confidence))
                except ValueError:
                    pass
            
            # Fallback to default confidence
            return 0.7
            
        except Exception as e:
            logger.warning(f"LLM confidence assessment failed: {e}")
            return 0.7
