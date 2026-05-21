import os
from tavily import TavilyClient

class ResearchTool:
    def __init__(self):
        # Ensure TAVILY_API_KEY is in your .env
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("TAVILY_API_KEY not found in environment")
        self.client = TavilyClient(api_key=api_key)

    def search(self, query: str):
        """Performs an advanced search and returns cleaned snippets."""
        try:
            # We use 'advanced' depth for better reasoning context
            response = self.client.search(
                query=query, 
                search_depth="advanced", 
                max_results=3
            )
            
            results = []
            for r in response.get('results', []):
                results.append(f"Source: {r['url']}\nSnippet: {r['content']}")
            
            return "\n\n".join(results) if results else "No external data found."
        except Exception as e:
            return f"Search failed: {str(e)}"