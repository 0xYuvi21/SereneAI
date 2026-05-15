from abc import ABC, abstractmethod
from typing import Any, Dict, AsyncGenerator


class IContextExtractor(ABC):
    @abstractmethod
    async def extract(self, request: Any) -> Dict[str, Any]:
        """Extracts context from the request."""
        pass


class IContextAggregator(ABC):
    @abstractmethod
    async def aggregate(self, extractions: Dict[str, Any]) -> str:
        """
        Aggregates extractions into a system prompt string.
        The prompt should NOT include the raw user message — that is passed
        separately to the responder as `human_message`.
        """
        pass


class ILLMResponder(ABC):
    @abstractmethod
    async def generate_response(
        self,
        system_prompt: str,
        human_message: str,
        user_id: str,
    ) -> AsyncGenerator[str, None]:
        """
        Generates a streaming response from the LLM.

        Args:
            system_prompt: Pre-built system context (sentiment, persona, etc.)
            human_message: The raw user input.
            user_id: Authenticated user's ID — passed through to MCP tool calls.
        """
        pass
