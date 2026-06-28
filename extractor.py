import re
import trafilatura

def is_url(text: str) -> bool:
    """Check if the provided text is a URL."""
    url_pattern = re.compile(
        r'^(https?://)?'
        r'(([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,})'
        r'(:\d+)?(/.*)?$'
    )
    return bool(url_pattern.match(text.strip()))

def extract_text(url: str) -> str:
    """Download and extract main article text from a URL."""
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded is None:
            return "Error: Could not fetch the webpage. It might be blocking scrapers."
        
        text = trafilatura.extract(downloaded)
        if text is None:
            return "Error: Could not extract readable text from the webpage."
            
        return text
    except Exception as e:
        return f"Error during extraction: {e}"
