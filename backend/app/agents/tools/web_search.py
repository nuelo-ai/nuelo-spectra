"""Web search tool for LangGraph agent tool-calling loop.

Defines the search_web @tool that the Data Analysis Agent can call
when web_search_enabled is True and the query warrants external data.
Uses SearchService for actual Serper.dev API calls and get_stream_writer()
for real-time SSE event emission.
"""

from langchain_core.tools import tool
from langgraph.config import get_stream_writer

from app.services.search import SearchService


@tool
async def search_web(query: str) -> str:
    """Search the web for information using Google Search.

    Use this tool when you need external data like industry benchmarks,
    market statistics, or comparative data that isn't in the uploaded dataset.

    Args:
        query: A generic search query (3-8 words). NEVER include specific
               company names, personal data, or raw values from the dataset.

    Returns:
        Search results as formatted text with titles and URLs.
    """
    writer = get_stream_writer()

    # Emit SSE event for real-time search activity display
    writer({"type": "search_started", "message": f"Searching: '{query}'..."})

    # Get search service (checks API key, returns None if not configured)
    service = SearchService.from_settings()
    if service is None:
        return "Web search is not configured. Answer from available data only."

    # Execute search
    result = await service.search(query)

    if not result.success:
        writer({"type": "search_failed", "message": "Web search unavailable"})
        return f"Search failed ({result.error}). Answer from available data only."

    # No results case
    if not result.results:
        return "No relevant search results found."

    # Format results for LLM consumption
    formatted = f"Search results for '{query}':\n"
    for r in result.results:
        formatted += f"- {r.title}: {r.link}\n"

    writer({
        "type": "search_completed",
        "message": f"Found {len(result.results)} results",
        "sources_count": len(result.results),
    })

    return formatted
