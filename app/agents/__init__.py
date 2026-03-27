from typing import Protocol, Dict, Any
from abc import ABC, abstractmethod

from ..schemas import AgentInput, AgentOutput


class Agent(Protocol):
    """Protocol that all agents must implement"""
    
    def process(self, input_data: AgentInput) -> AgentOutput:
        """Process input and return output"""
        ...
