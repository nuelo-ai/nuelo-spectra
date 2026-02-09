"""Web search service using Tavily API."""

import json
import logging
from dataclasses import dataclass

from tavily import AsyncTavilyClient

logger = logging.getLogger("spectra.search")


@dataclass
class SearchResult:
    """A single search result from Tavily."""

    title: str
    url: str


@dataclass
class SearchResponse:
    """Response from a web search query."""

    query: str
    results: list[SearchResult]
    answer: str | None
    success: bool
    error: str | None = None


class SearchService:
    """Tavily search API client.

    Provides async web search via Tavily Search API.
    Returns synthesized answer + source URLs for agent context.
    """

    def __init__(
        self,
        api_key: str,
        max_results: int = 3,
        search_depth: str = "basic",
        timeout: float = 10.0,
    ):
        self.client = AsyncTavilyClient(api_key=api_key)
        self.max_results = max_results
        self.search_depth = search_depth
        self.timeout = timeout

    @classmethod
    def from_settings(cls) -> "SearchService | None":
        """Create SearchService from app settings.

        Returns None if tavily_api_key is not configured (empty string).
        """
        from app.config import get_settings

        settings = get_settings()
        api_key = settings.tavily_api_key
        if not api_key:
            return None
        return cls(
            api_key=api_key,
            max_results=settings.search_num_results,
            search_depth=settings.search_depth,
            timeout=settings.search_timeout,
        )

    async def search(self, query: str) -> SearchResponse:
        """Execute a search query against Tavily.

        Args:
            query: The search query string.

        Returns:
            SearchResponse with results list, answer, success flag, and optional error.
        """
        try:
            response = await self.client.search(
                query=query,
                search_depth=self.search_depth,
                topic="general",
                max_results=self.max_results,
                include_answer=True,
                timeout=self.timeout,
            )

            answer = response.get("answer")
            raw_results = response.get("results", [])
            results = [
                SearchResult(
                    title=r.get("title", ""),
                    url=r.get("url", ""),
                )
                for r in raw_results
            ]

            logger.info(
                json.dumps(
                    {
                        "event": "web_search",
                        "query": query,
                        "results_count": len(results),
                        "has_answer": answer is not None,
                        "credits_used": 2 if self.search_depth == "advanced" else 1,
                        "status": "success",
                    }
                )
            )

            return SearchResponse(
                query=query,
                results=results,
                answer=answer,
                success=True,
            )

        except Exception as e:
            logger.error(
                json.dumps(
                    {
                        "event": "web_search",
                        "query": query,
                        "status": "error",
                        "error": str(e),
                    }
                )
            )
            return SearchResponse(
                query=query,
                results=[],
                answer=None,
                success=False,
                error=str(e),
            )
