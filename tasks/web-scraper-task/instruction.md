# Web Scraper Task

Create a Python script called `scraper.py` that:

1. Fetches the HTML content from `https://example.com`
2. Extracts the page title using BeautifulSoup
3. Saves the title to a file called `title.txt`

## Requirements

- Use the `requests` library to fetch the page
- Use `beautifulsoup4` to parse the HTML
- Handle errors gracefully (network errors, parsing errors)
- The output file should contain only the title text (no extra whitespace)

## Example Output

If the page title is "Example Domain", the `title.txt` file should contain:

```
Example Domain
```

## Notes

- All required libraries are pre-installed in the environment
- Write clean, well-commented code
- Test your script before marking the task complete
- Working directory is `/app`
