from flask import Flask, request, jsonify
from flask_cors import CORS
from scraper import LinkedInJobScraper
from multi_platform import JobScraper
import logging

app = Flask(__name__)
CORS(app)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.route('/')
def home():
   return jsonify({
        'message': 'Universal Job Scraper API (LinkedIn, Dice, Indeed)',
        'version': '1.1',
        'endpoints': {
            '/api/jobs': 'GET - Scrape jobs from LinkedIn',
            '/dice': 'GET - Scrape jobs from Dice.com',
            '/indeed': 'GET - Scrape jobs from Indeed.com', # <-- New Added
            'parameters': {
                'location': 'Required - Job location (e.g., Mumbai, Remote, TX, USA)',
                'keyword': 'Optional - Job keyword/title (e.g., Python Developer, Data Analyst)',
                'pages': 'Optional (LinkedIn only) - Number of pages to scrape',
                'days': 'Optional (LinkedIn only) - Filter jobs from last N days'
            }
        },
        'examples': {
            'linkedin': '/api/jobs?location=Mumbai&keyword=Python Developer&pages=5',
            'dice': '/dice?keyword=Python Developer&location=Remote',
            'indeed': '/indeed?keyword=Data Analyst&location=Remote' # <-- New Added
        },
        'note': 'Please respect robots.txt and terms of service of respective platforms. Use responsibly.'
    })

@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    try:
        location = request.args.get('location', '').strip()
        
        if not location:
            return jsonify({
                'success': False,
                'error': 'Location parameter is required',
                'example': '/api/jobs?location=Mumbai'
            }), 400
        
        keyword = request.args.get('keyword', '').strip()
        
        try:
            pages = int(request.args.get('pages', 3))
            pages = min(max(pages, 1), 10)
        except ValueError:
            pages = 3
        
        try:
            days = int(request.args.get('days', 7))
            days = max(days, 1)
        except ValueError:
            days = 7
        
        logger.info(f"API Request: location={location}, keyword={keyword or 'Any'}, pages={pages}, days={days}")
        
        scraper = LinkedInJobScraper(max_pages=pages, days_filter=days)
        result = scraper.scrape_jobs(location=location, keyword=keyword)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"API Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'LinkedIn Job Scraper API'
    }), 200

@app.route('/dice', methods=['GET'])
def get_dice_jobs():
    try:
        keyword = request.args.get('keyword', '').strip()
        location = request.args.get('location', '').strip()
        
        if not keyword:
            return jsonify({
                'success': False,
                'error': 'Keyword parameter is required',
                'example': '/dice?keyword=Python Developer&location=Remote'
            }), 400
        
        if not location:
            location = 'Remote'
        
        # Build Dice.com URL
        url = f"https://www.dice.com/jobs?q={keyword.replace(' ', '+')}&location={location.replace(' ', '+')}"
        
        logger.info(f"Dice API Request: keyword={keyword}, location={location}")
        
        # Scrape Dice jobs
        scraper = JobScraper()
        dice_jobs = scraper.dice_scrape(url)
        
        return jsonify({
            'success': True,
            'platform': 'Dice',
            'keyword': keyword,
            'location': location,
            'total_jobs': len(dice_jobs),
            'jobs': dice_jobs
        }), 200
        
    except Exception as e:
        logger.error(f"Dice API Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': str(e)
        }), 500

# --- NEW INDEED ROUTE ---
@app.route('/indeed', methods=['GET'])
def get_indeed_jobs():
    try:
        keyword = request.args.get('keyword', '').strip()
        location = request.args.get('location', '').strip()
        
        if not keyword:
            return jsonify({'error': 'Keyword required'}), 400
        
        if not location:
            location = 'Remote'
        
        # Indeed URL Format
        # q = keyword, l = location
        url = f"https://www.indeed.com/jobs?q={keyword.replace(' ', '+')}&l={location.replace(' ', '+')}"
        
        logger.info(f"Indeed Request: {url}")
        
        scraper = JobScraper()
        jobs = scraper.indeed_scrape(url)
        
        return jsonify({
            'success': True,
            'platform': 'Indeed',
            'total_jobs': len(jobs),
            'jobs': jobs
        }), 200
        
    except Exception as e:
        logger.error(f"Indeed API Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/ziprecruiter', methods=['GET'])
def get_zip_jobs():
    try:
        keyword = request.args.get('keyword', '').strip()
        location = request.args.get('location', '').strip()
        
        if not keyword:
            return jsonify({'error': 'Keyword required'}), 400
        
        if not location:
            location = 'India' # Default to India for ZipRecruiter.in
        
        # URL Construction
        # ZipRecruiter URL pattern: search?q=keyword&l=location
        url = f"https://www.ziprecruiter.in/jobs/search?q={keyword.replace(' ', '+')}&l={location.replace(' ', '+')}"
        
        logger.info(f"ZipRecruiter Request: {url}")
        
        scraper = JobScraper()
        jobs = scraper.ziprecruiter_scrape(url)
        
        return jsonify({
            'success': True,
            'platform': 'ZipRecruiter',
            'total_jobs': len(jobs),
            'jobs': jobs
        }), 200
        
    except Exception as e:
        logger.error(f"API Error: {str(e)}")
        return jsonify({'error': str(e)}), 500
        
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
