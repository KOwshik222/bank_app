"""
Base Agent class — foundation for all specialized AI investigation agents.
Provides LLM execution, evidence formatting, and structured output handling.
"""

import abc
import logging
from typing import Any

from ai.llm.ollama_client import LLMClient

logger = logging.getLogger(__name__)


class AgentResult:
    """Standard container for agent investigation findings."""

    def __init__(
        self,
        agent_name: str,
        hypothesis: str,
        confidence: float,
        evidence: list[str],
        data: dict[str, Any] | None = None,
        recommendation: str | None = None,
    ):
        self.agent_name = agent_name
        self.hypothesis = hypothesis
        self.confidence = round(confidence, 2)
        self.evidence = evidence
        self.data = data or {}
        self.recommendation = recommendation

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "hypothesis": self.hypothesis,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "data": self.data,
            "recommendation": self.recommendation,
        }


class BaseAgent(abc.ABC):
    """Abstract base agent."""

    def __init__(self, name: str, role_description: str):
        self.name = name
        self.role_description = role_description
        self.llm = LLMClient()

    @abc.abstractmethod
    async def investigate(self, context: dict[str, Any]) -> AgentResult:
        """Run agent investigation against incident context."""
        pass
