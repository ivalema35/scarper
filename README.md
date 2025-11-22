# LinkedIn Job Scraper API

A production-ready Flask-based REST API that scrapes LinkedIn job listings by location and returns structured JSON output with automatic pagination.

## Features

- 🔍 **Location-based job search** - Search jobs by any location
- 🔑 **Keyword filtering** - Optional job title/keyword search
- 📄 **Auto pagination** - Automatically scrapes multiple pages
- ✅ **Data validation** - Ensures required fields and removes duplicates
- 📅 **Date filtering** - Only shows jobs from last N days (configurable)
- 🔄 **Retry logic** - Handles timeouts and HTTP errors gracefully
- 🎭 **User-agent rotation** - Uses fake-useragent for reliability
- 📊 **JSON output** - Clean, structured JSON response
- 📝 **Comprehensive logging** - Detailed logs for debugging

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Or install manually:

```bash
pip install Flask flask-cors requests beautifulsoup4 fake-useragent lxml
```

### 2. Run the Server

```bash
python app.py
```

The API will start on `http://0.0.0.0:5000`

## API Endpoints

### Home - API Information
```
GET /
```

Returns API documentation and available endpoints.

### Get Jobs by Location
```
GET /api/jobs?location=<location>
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `location` | string | **Yes** | - | Job location (e.g., Mumbai, Delhi, Bangalore) |
| `keyword` | string | No | "" | Job keyword/title (e.g., Python Developer) |
| `pages` | integer | No | 3 | Number of pages to scrape (max: 10) |
| `days` | integer | No | 7 | Filter jobs from last N days |

#### Example Requests

**Simple location search:**
```bash
curl "http://localhost:5000/api/jobs?location=Mumbai"
```

**With keyword:**
```bash
curl "http://localhost:5000/api/jobs?location=Delhi&keyword=Python%20Developer"
```

**Custom pages and date filter:**
```bash
curl "http://localhost:5000/api/jobs?location=Bangalore&keyword=Data%20Analyst&pages=5&days=3"
```

#### Example Response

```json
{
  "success": true,
  "location": "Mumbai",
  "keyword": "Python Developer",
  "total_jobs": 45,
  "successful_pages": 3,
  "failed_pages": 0,
  "duration_seconds": 12.5,
  "start_time": "2025-11-22T10:30:00",
  "end_time": "2025-11-22T10:30:12",
  "jobs": [
    {
      "title": "Senior Python Developer",
      "company": "Tech Company Ltd",
      "location": "Mumbai, Maharashtra",
      "posted_date": "2 days ago",
      "apply_link": "https://www.linkedin.com/jobs/view/123456789"
    },
    {
      "title": "Python Backend Engineer",
      "company": "Startup Inc",
      "location": "Mumbai",
      "posted_date": "1 day ago",
      "apply_link": "https://www.linkedin.com/jobs/view/987654321"
    }
  ]
}
```

### Health Check
```
GET /health
```

Returns service health status.

## Project Structure

```
.
├── app.py              # Flask API server
├── scraper.py          # LinkedIn scraping logic
├── requirements.txt    # Python dependencies
└── README.md          # Documentation
```

## Features Details

### Scraper Module (`scraper.py`)

- **Automatic pagination**: Scrapes multiple pages without manual intervention
- **Smart retry logic**: Retries failed requests with exponential backoff
- **User-agent rotation**: Prevents blocking with random user agents
- **Date parsing**: Intelligently parses "2 days ago", "1 week ago", etc.
- **Duplicate removal**: Removes duplicate jobs based on title + company
- **Data validation**: Ensures all jobs have required fields
- **Error handling**: Graceful handling of timeouts and HTTP errors

### API Server (`app.py`)

- **RESTful API**: Clean REST endpoints with proper HTTP status codes
- **CORS enabled**: Allows cross-origin requests
- **Input validation**: Validates and sanitizes user inputs
- **Comprehensive logging**: Logs all requests and errors
- **Error responses**: Returns meaningful error messages

## Important Notes

### Ethical Scraping

⚠️ **Please use this tool responsibly:**

1. **Respect robots.txt**: Always check and respect LinkedIn's robots.txt
2. **Rate limiting**: Built-in delays between requests (2 seconds)
3. **Terms of Service**: Ensure compliance with LinkedIn's Terms of Service
4. **Legal compliance**: Web scraping may be subject to legal restrictions
5. **Personal use**: Intended for educational and personal use only

### Limitations

- LinkedIn may block requests if rate limits are exceeded
- HTML structure changes may break the scraper
- Some job details may not be available without authentication
- Public job listings only (no login-required jobs)

## Troubleshooting

### No jobs found?
- Check if the location name is correct
- LinkedIn might be blocking requests - try again later
- Reduce the number of pages to scrape

### Getting timeouts?
- Increase delay between requests in `scraper.py`
- Reduce the number of pages
- Check your internet connection

### Parsing errors?
- LinkedIn might have changed their HTML structure
- Update the CSS selectors in `_parse_jobs()` method

## Customization

### Change default pagination
Edit `app.py`:
```python
pages = int(request.args.get('pages', 5))  # Change default from 3 to 5
```

### Change delay between requests
Edit `scraper.py`:
```python
time.sleep(3)  # Change from 2 to 3 seconds
```

### Modify date filter
Edit `app.py`:
```python
days = int(request.args.get('days', 14))  # Change default from 7 to 14
```

## License

This project is provided as-is for educational purposes. Use responsibly and ensure compliance with all applicable laws and terms of service.

## Support

For issues or questions:
1. Check the logs for detailed error messages
2. Verify your internet connection
3. Ensure LinkedIn is accessible from your network
4. Review the troubleshooting section above
