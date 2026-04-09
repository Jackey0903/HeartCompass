"""ReAct agent loop for early prototype.
DEPRECATED: Will be replaced by LangGraph StateGraph.
"""
import asyncio
from typing import Any


class ReActAgent:
    """Simple ReAct (Reasoning + Acting) agent loop."""

    def __init__(self, llm, tools):
        self.llm = llm
        self.tools = tools

    async def run(self, query: str, max_steps: int = 10) -> dict[str, Any]:
        thought_history = []
        for step in range(max_steps):
            thought = await self.llm.think(query, thought_history)
            if thought.action == 'FINISH':
                return {"answer": thought.content, "steps": step + 1}
            result = await self.tools.execute(thought.action, thought.input)
            thought_history.append({
                "thought": thought.content,
                "action": thought.action,
                "observation": result,
            })
        return {"answer": "max steps reached", "steps": max_steps}
