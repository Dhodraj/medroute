import time
from datetime import datetime
from typing import Dict, Any
from loguru import logger

from .agents.intake_agent import IntakeAgent
from .agents.symptom_extraction_agent import SymptomExtractionAgent
from .agents.triage_agent import TriageAgent
from .agents.recommendation_agent import RecommendationAgent
from .agents.audit_agent import AuditAgent
from .schemas import AgentInput, AgentOutput, TriageRequest, TriageResponse, Symptom
from .models.model_factory import get_model


class TriageOrchestrator:
    """Orchestrates the agent chain for triage processing"""
    
    def __init__(self):
        # Initialize all agents
        self.intake_agent = IntakeAgent()
        self.symptom_extraction_agent = SymptomExtractionAgent()
        self.triage_agent = TriageAgent()
        self.recommendation_agent = RecommendationAgent()
        self.audit_agent = AuditAgent()
        
        # Get model info for metadata
        self.model = get_model()
        self.model_info = self.model.get_model_info()
        
    async def process_triage(self, request: TriageRequest) -> TriageResponse:
        """Process a triage request through the agent chain"""
        start_time = time.time()
        
        try:
            # Initialize agent input
            agent_input = AgentInput(
                query=request.query,
                metadata={
                    "model_info": self.model_info,
                    "start_time": start_time
                }
            )
            
            # Process through agent chain
            logger.info(f"Starting triage processing for query: {request.query[:50]}...")
            
            # 1. Intake Agent - validate and clean input
            logger.debug("Processing with IntakeAgent")
            agent_output = self.intake_agent.process(agent_input)
            agent_input = self._output_to_input(agent_output)
            
            # 2. Symptom Extraction Agent - extract symptoms
            logger.debug("Processing with SymptomExtractionAgent")
            agent_output = self.symptom_extraction_agent.process(agent_input)
            agent_input = self._output_to_input(agent_output)
            
            # 3. Triage Agent - determine triage level
            logger.debug("Processing with TriageAgent")
            agent_output = self.triage_agent.process(agent_input)
            agent_input = self._output_to_input(agent_output)
            
            # 4. Recommendation Agent - generate recommendations
            logger.debug("Processing with RecommendationAgent")
            agent_output = self.recommendation_agent.process(agent_input)
            agent_input = self._output_to_input(agent_output)
            
            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)
            agent_input.metadata["processing_time_ms"] = processing_time_ms
            
            # 5. Audit Agent - log the interaction
            logger.debug("Processing with AuditAgent")
            final_output = self.audit_agent.process(agent_input)
            
            # Create response
            response = TriageResponse(
                input=request.query,
                symptoms=final_output.symptoms,
                triage_level=final_output.triage_level,
                recommendation=final_output.recommendation,
                confidence_score=final_output.confidence_score,
                processing_time_ms=processing_time_ms
            )
            
            logger.info(f"Triage completed in {processing_time_ms}ms - Level: {final_output.triage_level}")
            return response
            
        except Exception as e:
            logger.error(f"Triage processing failed: {e}")
            
            # Calculate processing time even for errors
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Try to log the error
            try:
                error_input = AgentInput(
                    query=request.query,
                    metadata={
                        "error": str(e),
                        "processing_time_ms": processing_time_ms,
                        "model_info": self.model_info
                    }
                )
                self.audit_agent.process(error_input)
            except:
                pass  # Don't fail if audit logging fails
            
            # Return safe fallback response
            return TriageResponse(
                input=request.query,
                symptoms=[Symptom(name="processing error", severity="unknown")],
                triage_level="urgent",  # Safe default
                recommendation="Unable to process request. Please seek medical care. This is not a medical diagnosis. Consult a licensed doctor.",
                confidence_score=0.0,
                processing_time_ms=processing_time_ms
            )
    
    def _output_to_input(self, output: AgentOutput) -> AgentInput:
        """Convert agent output to input for next agent"""
        return AgentInput(
            query=output.query,
            symptoms=output.symptoms,
            triage_level=output.triage_level,
            recommendation=output.recommendation,
            confidence_score=output.confidence_score,
            metadata=output.metadata
        )
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get system health status"""
        try:
            model_available = self.model.is_available()
            
            return {
                "status": "healthy" if model_available else "degraded",
                "model": {
                    "available": model_available,
                    "info": self.model_info
                },
                "agents": {
                    "intake": "ready",
                    "symptom_extraction": "ready",
                    "triage": "ready", 
                    "recommendation": "ready",
                    "audit": "ready"
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
