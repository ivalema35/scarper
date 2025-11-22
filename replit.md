# LinkedIn Job Scraper API

## Project Overview
A production-ready Flask-based REST API that scrapes LinkedIn job listings by location and returns structured JSON output with automatic pagination.

**Created:** November 22, 2025  
**Language:** Python 3.11  
**Framework:** Flask  
**Purpose:** Web scraping tool for collecting job listings from LinkedIn

## Features
- Location-based job search
- Optional keyword filtering
- Automatic pagination (configurable pages)
- Data validation and duplicate removal
- Date filtering (last N days)
- Retry logic with exponential backoff
- User-agent rotation
- Comprehensive logging
- JSON output format

## Project Structure
```
.
├── app.py              # Flask API server with endpoints
├── scraper.py          # LinkedIn scraping logic
├── requirements.txt    # Python dependencies
├── README.md          # User documentation
└── .gitignore         # Git ignore file
```

## API Endpoints

### GET /
Returns API information and usage instructions

### GET /api/jobs
Main endpoint for scraping jobs

**Parameters:**
- `location` (required) - Job location (e.g., Mumbai, Delhi, Bangalore)
- `keyword` (optional) - Job keyword/title
- `pages` (optional) - Number of pages to scrape (default: 3, max: 10)
- `days` (optional) - Filter jobs from last N days (default: 7)

**Example:**
```bash
curl "http://localhost:5000/api/jobs?location=Mumbai&pages=2"
```

### GET /health
Health check endpoint

## Technical Details

### Scraper Module (scraper.py)
- **LinkedInJobScraper class** - Main scraper logic
- **Pagination handling** - Scrapes multiple pages automatically
- **Retry logic** - 3 retries with exponential backoff
- **User-agent rotation** - Random user agents to avoid blocking
- **Date parsing** - Handles "2 days ago", "1 week ago" formats
- **Duplicate removal** - Based on job title + company
- **Data validation** - Ensures required fields exist

### API Server (app.py)
- **Flask REST API** - Clean endpoints with proper HTTP status codes
- **CORS enabled** - Allows cross-origin requests
- **Input validation** - Validates and sanitizes inputs
- **Error handling** - Returns meaningful error messages
- **Logging** - Comprehensive request and error logging

## Dependencies
- Flask 3.1.2 - Web framework
- flask-cors 6.0.1 - CORS support
- requests 2.32.5 - HTTP requests
- beautifulsoup4 4.14.2 - HTML parsing
- fake-useragent 2.2.0 - User agent rotation
- lxml 5.3.0 - Parsing backend

## Usage

### Start the Server
The Flask server runs automatically on port 5000.

### Example API Calls

**Simple location search:**
```bash
curl "http://localhost:5000/api/jobs?location=Mumbai"
```

**With keyword:**
```bash
curl "http://localhost:5000/api/jobs?location=Delhi&keyword=Python Developer"
```

**Custom pages and date filter:**
```bash
curl "http://localhost:5000/api/jobs?location=Bangalore&pages=5&days=3"
```

## Response Format
```json
{
  "success": true,
  "location": "Mumbai",
  "keyword": "Any",
  "total_jobs": 45,
  "successful_pages": 3,
  "failed_pages": 0,
  "duration_seconds": 3.1,
  "start_time": "2025-11-22T08:59:08",
  "end_time": "2025-11-22T08:59:11",
  "jobs": [
    {
      "title": "Job Title",
      "company": "Company Name",
      "location": "City, State, Country",
      "posted_date": "2025-11-18",
      "apply_link": "https://linkedin.com/..."
    }
  ]
}
```

## Important Notes

### Ethical Usage
- Respect LinkedIn's robots.txt and terms of service
- Built-in rate limiting (2 seconds between requests)
- Use responsibly for personal/educational purposes only
- Consider legal implications of web scraping

### Limitations
- Public job listings only (no authentication)
- LinkedIn may block excessive requests
- HTML structure changes may break selectors
- Some job details may be incomplete

## Recent Changes
- **2025-11-22:** Initial project creation
  - Created Flask API with /api/jobs endpoint
  - Implemented LinkedIn job scraper with pagination
  - Added retry logic and error handling
  - Created comprehensive documentation

## Architecture Decisions
- **Flask over FastAPI**: Simple, lightweight, well-suited for this use case
- **BeautifulSoup over Scrapy**: Easier to maintain for single-page scraping
- **Session management**: Reuses HTTP connections for better performance
- **Synchronous scraping**: Simple, reliable, sufficient for current needs
- **In-memory processing**: No database needed for stateless API

## Configuration
- **Default pages**: 3 (configurable via API parameter)
- **Max pages**: 10 (hard limit to prevent abuse)
- **Default days filter**: 7 days
- **Request timeout**: 15 seconds
- **Retry attempts**: 3 with exponential backoff
- **Delay between requests**: 2 seconds

## Future Enhancements
- Async scraping with aiohttp for faster performance
- Database storage for historical job tracking
- Job change detection and notifications
- Support for more job boards (Indeed, Glassdoor)
- Caching layer to avoid re-scraping
- Authentication for protected listings
