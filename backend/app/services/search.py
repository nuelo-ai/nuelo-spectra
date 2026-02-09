"""Web search service using Serper.dev API."""

import json
import logging
from dataclasses import dataclass

import httpx

logger = logging.getLogger("spectra.search")


@dataclass
class SearchResult:
    """A single search result from Serper.dev."""

    title: str
    link: str
    position: int


@dataclass
class SearchResponse:
    """Response from a web search query."""

    query: str
    results: list[SearchResult]
    success: bool
    error: str | None = None


class SearchService:
    """Serper.dev search API client.

    Provides async web search via Serper.dev Google Search API.
    Supports configurable result count, domain blocking, and timeout.
    """

    BASE_URL = "https://google.serper.dev/search"

    def __init__(
        self,
        api_key: str,
        num_results: int = 5,
        blocked_domains: list[str] | None = None,
        timeout: float = 10.0,
    ):
        self.api_key = api_key
        self.num_results = num_results
        self.blocked_domains = blocked_domains or []
        self.timeout = timeout

    @classmethod
    def from_settings(cls) -> "SearchService | None":
        """Create SearchService from app settings.

        Returns None if serper_api_key is not configured (empty string).
        """
        from app.config import get_settings

        settings = get_settings()
        api_key = settings.serper_api_key
        if not api_key:
            return None
        return cls(
            api_key=api_key,
            num_results=settings.search_num_results,
            timeout=settings.search_timeout,
        )

    async def search(self, query: str) -> SearchResponse:
        """Execute a search query against Serper.dev.

        Args:
            query: The search query string.

        Returns:
            SearchResponse with results list, success flag, and optional error.
        """
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {"q": query, "num": self.num_results}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.BASE_URL,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                data = response.json()

            organic = data.get("organic", [])
            results = []
            for item in organic:
                link = item.get("link", "")
                # Filter out blocked domains
                if any(domain in link for domain in self.blocked_domains):
                    continue
                results.append(
                    SearchResult(
                        title=item.get("title", ""),
                        link=link,
                        position=item.get("position", 0),
                    )
                )

            logger.info(
                json.dumps(
                    {
                        "event": "web_search",
                        "query": query,
                        "results_count": len(results),
                        "status": "success",
                    }
                )
            )

            return SearchResponse(query=query, results=results, success=True)

        except httpx.TimeoutException:
            logger.warning(
                json.dumps(
                    {
                        "event": "web_search",
                        "query": query,
                        "status": "timeout",
                    }
                )
            )
            return SearchResponse(
                query=query, results=[], success=False, error="timeout"
            )
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            logger.error(
                json.dumps(
                    {
                        "event": "web_search",
                        "query": query,
                        "status": "http_error",
                        "code": status_code,
                    }
                )
            )
            return SearchResponse(
                query=query,
                results=[],
                success=False,
                error=f"HTTP {status_code}",
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
                query=query, results=[], success=False, error=str(e)
            )
