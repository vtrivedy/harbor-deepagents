#!/bin/bash
# Reference solution for the web scraper task

cat > /app/scraper.py << 'EOF'
"""Web scraper that extracts title from example.com"""
import requests
from bs4 import BeautifulSoup


def scrape_title(url: str) -> str:
    """Fetch and extract title from a webpage.

    Args:
        url: The URL to scrape

    Returns:
        The page title or an error message
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        title = soup.find('title')

        if title:
            return title.get_text().strip()
        else:
            return "No title found"
    except Exception as e:
        return f"Error: {e}"


if __name__ == "__main__":
    url = "https://example.com"
    title = scrape_title(url)

    with open("/app/title.txt", "w") as f:
        f.write(title)

    print(f"Title saved: {title}")
EOF

# Run the scraper
python /app/scraper.py

echo "Solution complete!"
