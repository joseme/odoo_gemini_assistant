import requests
import logging
from urllib.parse import quote

_logger = logging.getLogger(__name__)


class WebSearchService:
    """Service to perform web searches using DuckDuckGo."""

    def __init__(self, enabled=True):
        """
        Initialize web search service.
        
        Args:
            enabled: Whether to enable web search
        """
        self.enabled = enabled
        self.base_url = "https://api.duckduckgo.com/"

    def search(self, query, max_results=5):
        """
        Search the web using DuckDuckGo.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            dict with keys:
            - success: bool
            - results: list of dicts with 'title', 'url', 'snippet'
            - error: str (if failed)
        """
        if not self.enabled:
            return {
                "success": False,
                "results": [],
                "error": "Web search is disabled",
            }

        try:
            params = {
                "q": query,
                "format": "json",
                "no_html": 1,
                "skip_disambig": 1,
            }

            response = requests.get(
                self.base_url,
                params=params,
                timeout=10,
                headers={"User-Agent": "OdooGeminiAssistant/1.0"},
            )

            if response.status_code == 200:
                data = response.json()
                
                results = []
                
                # Get results from DuckDuckGo
                if "Results" in data:
                    for item in data["Results"][:max_results]:
                        results.append({
                            "title": item.get("Title", ""),
                            "url": item.get("FirstURL", ""),
                            "snippet": item.get("Result", ""),
                        })
                
                return {
                    "success": True,
                    "results": results,
                }
            else:
                error_msg = f"DuckDuckGo API error: {response.status_code}"
                _logger.warning(error_msg)
                return {
                    "success": False,
                    "results": [],
                    "error": error_msg,
                }

        except requests.exceptions.Timeout:
            error_msg = "Web search timeout"
            _logger.warning(error_msg)
            return {
                "success": False,
                "results": [],
                "error": error_msg,
            }
        except requests.exceptions.ConnectionError:
            error_msg = "Cannot connect to web search service"
            _logger.warning(error_msg)
            return {
                "success": False,
                "results": [],
                "error": error_msg,
            }
        except Exception as e:
            error_msg = f"Web search error: {str(e)}"
            _logger.error(error_msg)
            return {
                "success": False,
                "results": [],
                "error": error_msg,
            }

    def format_results_for_context(self, results):
        """
        Format search results as context string for Gemini.
        
        Args:
            results: List of search results
            
        Returns:
            Formatted string with search results
        """
        if not results:
            return ""
        
        formatted = "Web Search Results:\n"
        for i, result in enumerate(results, 1):
            formatted += f"\n{i}. {result.get('title', 'Untitled')}\n"
            formatted += f"   URL: {result.get('url', 'N/A')}\n"
            formatted += f"   {result.get('snippet', 'No description')}\n"
        
        return formatted
