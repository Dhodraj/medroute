import pytest
import asyncio
from app.schemas import TriageRequest, TriageResponse, Symptom, TriageLevel
from app.orchestrator import TriageOrchestrator


@pytest.fixture
def orchestrator():
    """Create a test orchestrator instance"""
    return TriageOrchestrator()


@pytest.mark.asyncio
async def test_chest_pain_emergency():
    """Test chest pain triggers emergency triage"""
    orchestrator = TriageOrchestrator()
    request = TriageRequest(query="I have severe chest pain for 2 hours")
    
    response = await orchestrator.process_triage(request)
    
    assert response.triage_level == TriageLevel.EMERGENCY
    assert "chest pain" in response.symptoms[0].name.lower()
    assert "emergency" in response.recommendation.lower()


@pytest.mark.asyncio
async def test_mild_headache():
    """Test mild headache gets appropriate triage level"""
    orchestrator = TriageOrchestrator()
    request = TriageRequest(query="I have a mild headache")
    
    response = await orchestrator.process_triage(request)
    
    assert response.triage_level in [TriageLevel.NON_URGENT, TriageLevel.SEMI_URGENT]
    assert len(response.symptoms) > 0


@pytest.mark.asyncio
async def test_empty_query():
    """Test empty query validation"""
    orchestrator = TriageOrchestrator()
    
    with pytest.raises(ValueError):
        request = TriageRequest(query="")
        await orchestrator.process_triage(request)


@pytest.mark.asyncio
async def test_very_long_query():
    """Test query length truncation"""
    orchestrator = TriageOrchestrator()
    long_query = "pain " * 1000  # Very long query
    request = TriageRequest(query=long_query)
    
    response = await orchestrator.process_triage(request)
    
    # Should still process but truncate
    assert response is not None
    assert len(response.input) <= 2000


def test_health_status():
    """Test health status endpoint"""
    orchestrator = TriageOrchestrator()
    health = orchestrator.get_health_status()
    
    assert "status" in health
    assert "model" in health
    assert "agents" in health


@pytest.mark.asyncio
async def test_multiple_symptoms():
    """Test extraction of multiple symptoms"""
    orchestrator = TriageOrchestrator()
    request = TriageRequest(query="I have chest pain and shortness of breath for 1 hour")
    
    response = await orchestrator.process_triage(request)
    
    assert response.triage_level == TriageLevel.EMERGENCY
    assert len(response.symptoms) >= 1  # Should extract at least one symptom


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
