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
        'message': 'LinkedIn Job Scraper API',
        'version': '1.0',
        'endpoints': {
            '/api/jobs': 'GET - Scrape jobs by location',
            '/dice': 'GET - Scrape jobs from Dice.com',
            'parameters': {
                'location': 'Required - Job location (e.g., Mumbai, Delhi, Bangalore)',
                'keyword': 'Optional - Job keyword/title (e.g., Python Developer, Data Analyst)',
                'pages': 'Optional - Number of pages to scrape (default: 3, max: 10)',
                'days': 'Optional - Filter jobs from last N days (default: 7)'
            }
        },
        'example': '/api/jobs?location=Mumbai&keyword=Python Developer&pages=5&days=7',
        'dice_example': '/dice?keyword=Python Developer&location=Remote',
        'note': 'Please respect LinkedIn robots.txt and terms of service. Use responsibly.'
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
