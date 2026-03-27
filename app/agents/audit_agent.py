import json
from datetime import datetime
from typing import List, Dict, Any
from loguru import logger

from . import Agent
from ..schemas import AgentInput, AgentOutput, LogEntry
from ..database.database import DatabaseManager


class AuditAgent:
    """Agent responsible for logging and auditing triage interactions"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        
    def process(self, input_data: AgentInput) -> AgentOutput:
        """Log the triage interaction to database"""
        try:
            # Create log entry
            log_entry = LogEntry(
                input_text=input_data.query,
                symptoms=json.dumps([symptom.dict() for symptom in input_data.symptoms]),
                triage_level=self._get_triage_level_value(input_data.triage_level),
                recommendation=input_data.recommendation or "",
                confidence_score=input_data.confidence_score,
                model_version=self._get_model_version(input_data.metadata),  # Use alias field name
                processing_time_ms=input_data.metadata.get("processing_time_ms"),
                timestamp=datetime.utcnow()
            )
            
            # Save to database
            log_id = self.db_manager.save_log_entry(log_entry)
            
            # Update metadata with audit info
            metadata = input_data.metadata.copy()
            metadata.update({
                "audit_agent": {
                    "log_id": log_id,
                    "logged_at": datetime.utcnow().isoformat(),
                    "status": "success"
                }
            })
            
            logger.info(f"Triage interaction logged with ID: {log_id}")
            
            return AgentOutput(
                query=input_data.query,
                symptoms=input_data.symptoms,
                triage_level=input_data.triage_level,
                recommendation=input_data.recommendation,
                confidence_score=input_data.confidence_score,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"AuditAgent error: {e}")
            
            # Update metadata with error info
            metadata = input_data.metadata.copy()
            metadata.update({
                "audit_agent": {
                    "status": "failed",
                    "error": str(e),
                    "logged_at": datetime.utcnow().isoformat()
                }
            })
            
            # Return original data even if logging fails
            return AgentOutput(
                query=input_data.query,
                symptoms=input_data.symptoms,
                triage_level=input_data.triage_level,
                recommendation=input_data.recommendation,
                confidence_score=input_data.confidence_score,
                metadata=metadata
            )
    
    def _get_triage_level_value(self, triage_level) -> str:
        """Safely extract triage level value"""
        if triage_level is None:
            return "unknown"
        
        # Handle TriageLevel enum
        if hasattr(triage_level, 'value'):
            return triage_level.value
        
        # Handle string
        if isinstance(triage_level, str):
            return triage_level
            
        # Fallback
        return str(triage_level)
    
    def _get_model_version(self, metadata: Dict[str, Any]) -> str:
        """Extract model version from metadata"""
        try:
            # Try to get model info from metadata
            if "model_info" in metadata:
                return metadata["model_info"].get("name", "unknown")
            
            # Default model version from settings
            from ..config import get_settings
            settings = get_settings()
            return settings.ollama_model
            
        except Exception:
            return "unknown"
    
    def get_recent_logs(self, limit: int = 10) -> List[LogEntry]:
        """Get recent log entries for monitoring"""
        try:
            return self.db_manager.get_recent_logs(limit)
        except Exception as e:
            logger.error(f"Failed to retrieve recent logs: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get audit statistics"""
        try:
            return self.db_manager.get_stats()
        except Exception as e:
            logger.error(f"Failed to retrieve stats: {e}")
            return {}
