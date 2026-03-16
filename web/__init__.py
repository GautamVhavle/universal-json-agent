"""
Web Server — FastAPI + LangChain interface for JSON Agent.

A standalone REST API that accepts a JSON file + natural language query,
uses an LLM (via OpenRouter) to autonomously pick and chain the right
JSON analysis tools, and returns the final answer.
"""
