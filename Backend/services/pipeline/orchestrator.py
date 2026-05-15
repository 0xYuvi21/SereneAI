from Backend.services.pipeline.interfaces import IContextExtractor, IContextAggregator, ILLMResponder
from typing import Any, List
import asyncio


class ChatPipeline:
    def __init__(
        self,
        extractors: List[IContextExtractor],
        aggregator: IContextAggregator,
        responder: ILLMResponder,
    ):
        self.extractors = extractors
        self.aggregator = aggregator
        self.responder = responder

    async def execute(self, request: Any, user_id: str = "") -> str:
        # 1. Run all context extractors concurrently
        tasks = [e.extract(request) for e in self.extractors]
        results = await asyncio.gather(*tasks)

        # 2. Merge extraction dicts
        extractions: dict = {"user_id": user_id}
        for res in results:
            extractions.update(res)

        # 3. Build system prompt
        system_prompt = await self.aggregator.aggregate(extractions)

        # 4. Pull the raw user message for the HumanMessage slot
        human_message: str = extractions.get("message", "")

        # 5. Collect all tokens from the agent into a full response string
        full_response = ""
        async for token in self.responder.generate_response(
            system_prompt=system_prompt,
            human_message=human_message,
            user_id=user_id,
        ):
            full_response += token

        return full_response
