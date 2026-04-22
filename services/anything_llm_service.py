import requests
import logging

_logger = logging.getLogger(__name__)


class AnythingLLMService:
    """Service to interact with AnythingLLM workspace."""

    def __init__(self, base_url, api_key, workspace_name):
        """
        Initialize AnythingLLM service.
        
        Args:
            base_url: Base URL of AnythingLLM instance (e.g., http://info.knowhub.tech)
            api_key: API key for authentication
            workspace_name: Name of the workspace (e.g., "Odoo17")
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.workspace_name = workspace_name
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def query_workspace(self, query, top_k=5):
        """
        Query the AnythingLLM workspace for relevant documentation.
        
        Args:
            query: User question or search query
            top_k: Number of top results to return
            
        Returns:
            dict with keys:
            - success: bool
            - context: str (concatenated relevant documents)
            - sources: list (metadata about sources)
            - error: str (if failed)
        """
        try:
            url = f"{self.base_url}/api/v1/workspace/{self.workspace_name}/chat"
            
            payload = {
                "message": query,
                "mode": "query",  # Query mode to get context without full chat
            }

            response = requests.post(
                url,
                json=payload,
                headers=self.headers,
                timeout=30,
            )

            if response.status_code == 200:
                data = response.json()
                
                # Extract context and sources from response
                context = data.get("context", "")
                sources = data.get("sources", [])
                
                return {
                    "success": True,
                    "context": context,
                    "sources": sources,
                    "message": data.get("message", ""),
                }
            else:
                error_msg = f"AnythingLLM API error: {response.status_code} - {response.text}"
                _logger.warning(error_msg)
                return {
                    "success": False,
                    "context": "",
                    "sources": [],
                    "error": error_msg,
                }

        except requests.exceptions.Timeout:
            error_msg = "AnythingLLM request timeout"
            _logger.warning(error_msg)
            return {
                "success": False,
                "context": "",
                "sources": [],
                "error": error_msg,
            }
        except requests.exceptions.ConnectionError:
            error_msg = "Cannot connect to AnythingLLM"
            _logger.warning(error_msg)
            return {
                "success": False,
                "context": "",
                "sources": [],
                "error": error_msg,
            }
        except Exception as e:
            error_msg = f"AnythingLLM error: {str(e)}"
            _logger.error(error_msg)
            return {
                "success": False,
                "context": "",
                "sources": [],
                "error": error_msg,
            }

    def is_configured(self):
        """Check if AnythingLLM is properly configured."""
        return bool(self.base_url and self.api_key and self.workspace_name)
