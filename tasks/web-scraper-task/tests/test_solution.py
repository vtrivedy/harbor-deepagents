"""Tests for the web scraper task."""

from pathlib import Path


def test_scraper_file_exists():
    """Test that scraper.py exists."""
    scraper_path = Path("/app/scraper.py")
    assert scraper_path.exists(), "scraper.py file does not exist"


def test_title_file_exists():
    """Test that title.txt was created."""
    title_path = Path("/app/title.txt")
    assert title_path.exists(), "title.txt file does not exist"


def test_title_file_not_empty():
    """Test that title.txt is not empty."""
    title_path = Path("/app/title.txt")
    content = title_path.read_text().strip()
    assert len(content) > 0, "title.txt is empty"


def test_title_content_valid():
    """Test that title.txt contains expected content."""
    title_path = Path("/app/title.txt")
    content = title_path.read_text().strip()

    # example.com's title is "Example Domain"
    assert "Example Domain" in content, f"Unexpected title: {content}"


def test_scraper_imports():
    """Test that scraper.py has required imports."""
    scraper_path = Path("/app/scraper.py")
    content = scraper_path.read_text()

    assert "requests" in content, "scraper.py must import requests"
    assert "BeautifulSoup" in content or "beautifulsoup" in content.lower(), \
        "scraper.py must import BeautifulSoup"


def test_scraper_is_valid_python():
    """Test that scraper.py is valid Python syntax."""
    scraper_path = Path("/app/scraper.py")
    content = scraper_path.read_text()

    try:
        compile(content, scraper_path, 'exec')
    except SyntaxError as e:
        assert False, f"scraper.py has syntax error: {e}"
