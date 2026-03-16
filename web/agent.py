"""
LangChain Agent — autonomous JSON analysis powered by an LLM.

Creates a ReAct-style agent that can pick and chain any combination of the
26 JSON tools to answer a user question.

Provider compatibility:
        - This agent layer is LangChain-native and provider-agnostic.
        - It works with any LangChain chat model integration (OpenAI,
            Anthropic/Claude, Azure OpenAI, OpenRouter, etc.).
        - This project currently wires the default client via OpenRouter using
            `langchain_openai.ChatOpenAI` and an OpenAI-compatible base URL.

Architecture:
    - The LLM client is created once and reused (expensive to init).
    - A fresh JSONStore + tool set is built per request (cheap, ensures isolation).
    - The LangGraph ReAct agent is built per request because tools are bound
      to the per-request store (LangGraph compiles fast, this is fine).
"""

from __future__ import annotations

import logging
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.prebuilt import create_react_agent

from universal_json_agent_mcp.store import JSONStore
from web.config import settings
from web.tools import build_tools

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# System prompt — tells the LLM how to use the JSON tools
# ------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are an expert JSON data analyst. You have access to a set of tools that \
let you load, explore, query, aggregate, transform, and export JSON documents.

## Workflow
1. The user will provide a JSON file path and a question.
2. FIRST call `load_json` with the file path to load it into memory.
3. Then call `get_structure` to understand the document shape.
4. Use the appropriate tools to answer the question — you may chain multiple \
tool calls as needed.
5. When you have the answer, respond with a clear, concise summary.

## Critical: Use Bulk Extraction — NEVER Iterate One-by-One
- When you need data from every item in an array, use a SINGLE `jsonpath_query` \
call with a wildcard expression like `$.missions[*].name` instead of looping \
through indices one at a time.
- Use `pick_fields` to extract multiple fields from every object in one call.
- Use `filter_objects` to select items matching a condition in one call.
- NEVER call `get_value` in a loop for each array index — this wastes tool \
calls and is extremely slow. Always prefer bulk tools.

## Rules
- Always load the file before doing anything else.
- Prefer specific tools over brute-force (e.g. use `filter_objects` instead \
of fetching everything and filtering manually).
- Use `jsonpath_query` with wildcards (`[*]`, `..`) for bulk extraction.
- Use `pick_fields` to grab specific fields from every object at a path.
- Use `search_text` when you need to find where a value lives.
- Use `describe` / `sum_values` / `min_max` / `value_counts` for analytics.
- If a tool returns an error, try an alternative approach.
- Keep your final answer focused — answer exactly what was asked.
- Aim to finish in as few tool calls as possible (typically 3-6).
"""


def create_llm() -> ChatOpenAI:
    """
        Create the shared LLM client (reused across requests).

        Notes:
                - Default wiring uses OpenRouter through an OpenAI-compatible endpoint.
                - You can swap this with any LangChain chat model class (for example,
                    OpenAI, Claude, or Azure OpenAI integrations) without changing the
                    rest of the agent flow.

    Raises:
        ValueError: If OPENROUTER_API_KEY is not set.
    """
    if not settings.openrouter_api_key:
        raise ValueError(
            "OPENROUTER_API_KEY is not set. "
            "Set it in your environment or in a .env file."
        )

    return ChatOpenAI(
        model=settings.openrouter_model,
        openai_api_key=settings.openrouter_api_key,
        openai_api_base=settings.openrouter_base_url,
        temperature=0,
        max_retries=2,
    )


def create_agent_for_request(llm: ChatOpenAI) -> tuple[Any, JSONStore]:
    """
    Create a per-request agent with its own isolated JSONStore.

    This ensures concurrent requests never share document state.

    Args:
        llm: The shared LLM client.

    Returns:
        A tuple of (CompiledStateGraph, JSONStore).
    """
    store = JSONStore()
    tools = build_tools(store)

    graph = create_react_agent(
        model=llm,
        tools=tools,
        prompt=SYSTEM_PROMPT,
    )

    return graph, store


async def run_query(
    llm: ChatOpenAI,
    question: str,
    file_path: str,
) -> dict[str, Any]:
    """
    Run a natural-language query against a JSON file.

    Creates an isolated agent per call — the JSONStore is discarded
    after the query completes, preventing cross-request data leaks.

    Returns:
        A dict with keys: "answer", "steps" (list of tool calls made).
    """
    logger.info("Query: %s | File: %s", question, file_path)

    graph, store = create_agent_for_request(llm)

    augmented_input = (
        f"The JSON file is located at: {file_path}\n\n"
        f"Question: {question}"
    )

    try:
        result = await graph.ainvoke(
            {"messages": [HumanMessage(content=augmented_input)]},
            config={"recursion_limit": settings.max_iterations},
        )
    finally:
        # Ensure all loaded documents are freed after the request
        for meta in store.list_loaded():
            try:
                store.unload(meta.alias)
            except Exception:
                pass

    # Extract tool calls from intermediate messages
    steps: list[dict[str, Any]] = []
    answer = ""

    for msg in result.get("messages", []):
        # ToolMessage instances have a .name attribute
        if hasattr(msg, "name") and getattr(msg, "name", None):
            steps.append({
                "tool": msg.name,
                "output": str(msg.content)[:500],
            })
            logger.info("  Tool call: %s", msg.name)
        # The last AI message without tool_calls is the final answer
        if isinstance(msg, AIMessage) and msg.content and not getattr(msg, "tool_calls", None):
            answer = msg.content

    logger.info("  Answer length: %d chars | Steps: %d", len(answer), len(steps))

    return {
        "answer": answer,
        "steps": steps,
    }
