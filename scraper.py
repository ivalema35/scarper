import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import re

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LinkedInJobScraper:
    def __init__(self, max_pages: int = 3, days_filter: int = 7):
        self.max_pages = max_pages
        self.days_filter = days_filter
        self.ua = UserAgent()
        self.session = requests.Session()
        self.jobs_data = []
        
    def _get_headers(self) -> Dict[str, str]:
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    def _fetch_page(self, url: str, retries: int = 3) -> Optional[str]:
        response = None
        for attempt in range(retries):
            try:
                logger.info(f"Fetching URL: {url} (Attempt {attempt + 1}/{retries})")
                response = self.session.get(
                    url,
                    headers=self._get_headers(),
                    timeout=15
                )
                response.raise_for_status()
                
                if response.status_code == 200:
                    logger.info(f"Successfully fetched page (Status: {response.status_code})")
                    return response.text
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout on attempt {attempt + 1}")
                time.sleep(2 ** attempt)
                
            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP error on attempt {attempt + 1}: {e}")
                if response and response.status_code == 429:
                    time.sleep(5 * (attempt + 1))
                else:
                    time.sleep(2 ** attempt)
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error on attempt {attempt + 1}: {e}")
                time.sleep(2 ** attempt)
                
        logger.error(f"Failed to fetch page after {retries} attempts")
        return None
    
    def _normalize_text(self, text: str) -> str:
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _parse_posted_date(self, date_text: str) -> Optional[datetime]:
        if not date_text:
            return None
            
        date_text_normalized = self._normalize_text(date_text)
        
        try:
            if re.match(r'^\d{4}-\d{2}-\d{2}', date_text_normalized):
                return datetime.fromisoformat(date_text_normalized.split('T')[0])
        except (ValueError, AttributeError):
            pass
        
        date_text_lower = date_text_normalized.lower()
        
        try:
            if 'just now' in date_text_lower or 'today' in date_text_lower:
                return datetime.now()
            elif 'yesterday' in date_text_lower:
                return datetime.now() - timedelta(days=1)
            elif 'hour' in date_text_lower or 'hr' in date_text_lower:
                match = re.search(r'(\d+)', date_text_lower)
                hours = int(match.group(1)) if match else 1
                return datetime.now() - timedelta(hours=hours)
            elif 'day' in date_text_lower or 'days' in date_text_lower:
                match = re.search(r'(\d+)', date_text_lower)
                days = int(match.group(1)) if match else 1
                return datetime.now() - timedelta(days=days)
            elif 'week' in date_text_lower or 'weeks' in date_text_lower:
                match = re.search(r'(\d+)', date_text_lower)
                weeks = int(match.group(1)) if match else 1
                return datetime.now() - timedelta(weeks=weeks)
            elif 'month' in date_text_lower or 'months' in date_text_lower:
                match = re.search(r'(\d+)', date_text_lower)
                months = int(match.group(1)) if match else 1
                return datetime.now() - timedelta(days=months * 30)
        except:
            pass
            
        return None
    
    def _is_recent_job(self, posted_date: Optional[datetime]) -> bool:
        if not posted_date:
            return True
        
        cutoff_date = datetime.now() - timedelta(days=self.days_filter)
        return posted_date >= cutoff_date
    
    def _parse_jobs(self, html: str) -> List[Dict]:
        soup = BeautifulSoup(html, 'lxml')
        jobs = []
        
        job_cards = soup.find_all('div', class_='base-card')
        if not job_cards:
            job_cards = soup.find_all('li', class_='jobs-search-results__list-item')
        if not job_cards:
            job_cards = soup.find_all('div', class_='job-search-card')
        
        logger.info(f"Found {len(job_cards)} job cards on this page")
        
        for card in job_cards:
            try:
                job = {}
                
                title_elem = card.find('h3', class_='base-search-card__title') or \
                            card.find('a', class_='base-card__full-link') or \
                            card.find('h3')
                            
                if title_elem:
                    job['title'] = self._normalize_text(title_elem.get_text())
                
                company_elem = card.find('h4', class_='base-search-card__subtitle') or \
                              card.find('a', class_='hidden-nested-link') or \
                              card.find('h4')
                              
                if company_elem:
                    job['company'] = self._normalize_text(company_elem.get_text())
                
                location_elem = card.find('span', class_='job-search-card__location') or \
                               card.find('span', class_='job-result-card__location')
                               
                if location_elem:
                    job['location'] = self._normalize_text(location_elem.get_text())
                
                date_elem = card.find('time') or \
                           card.find('span', class_='job-search-card__listdate')
                           
                if date_elem:
                    datetime_attr = date_elem.get('datetime', '')
                    date_text = str(datetime_attr) if datetime_attr else date_elem.get_text()
                    job['posted_date'] = self._normalize_text(date_text)
                    posted_datetime = self._parse_posted_date(date_text)
                    
                    if not self._is_recent_job(posted_datetime):
                        logger.debug(f"Skipping old job: {job.get('title', 'Unknown')}")
                        continue
                
                link_elem = card.find('a', class_='base-card__full-link') or \
                           card.find('a', href=True)
                           
                if link_elem:
                    href_attr = link_elem.get('href', '')
                    job['apply_link'] = str(href_attr).strip() if href_attr else ''
                    if job['apply_link'] and not job['apply_link'].startswith('http'):
                        job['apply_link'] = 'https://www.linkedin.com' + job['apply_link']
                
                if job.get('title') and job.get('company'):
                    jobs.append(job)
                    logger.debug(f"Parsed job: {job['title']} at {job['company']}")
                else:
                    logger.debug("Skipping job card due to missing required fields")
                    
            except Exception as e:
                logger.error(f"Error parsing job card: {e}")
                continue
        
        return jobs
    
    def _remove_duplicates(self, jobs: List[Dict]) -> List[Dict]:
        seen = set()
        unique_jobs = []
        
        for job in jobs:
            job_key = (job.get('title', '').lower(), job.get('company', '').lower())
            
            if job_key not in seen and job_key != ('', ''):
                seen.add(job_key)
                unique_jobs.append(job)
        
        logger.info(f"Removed {len(jobs) - len(unique_jobs)} duplicate jobs")
        return unique_jobs
    
    def scrape_jobs(self, location: str, keyword: str = "") -> Dict:
        start_time = datetime.now()
        logger.info(f"Starting job scraping for location: {location}, keyword: {keyword or 'Any'}")
        
        all_jobs = []
        successful_pages = 0
        failed_pages = 0
        
        for page in range(self.max_pages):
            start_index = page * 25
            
            if keyword:
                url = f"https://www.linkedin.com/jobs/search?keywords={keyword}&location={location}&start={start_index}"
            else:
                url = f"https://www.linkedin.com/jobs/search?location={location}&start={start_index}"
            
            html = self._fetch_page(url)
            
            if html:
                jobs = self._parse_jobs(html)
                all_jobs.extend(jobs)
                successful_pages += 1
                logger.info(f"Page {page + 1}: Found {len(jobs)} jobs")
                
                if len(jobs) == 0 and page > 0:
                    logger.info("No more jobs found, stopping pagination")
                    break
            else:
                failed_pages += 1
                logger.warning(f"Failed to fetch page {page + 1}")
            
            time.sleep(2)
        
        unique_jobs = self._remove_duplicates(all_jobs)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        is_success = successful_pages > 0
        
        result = {
            'success': is_success,
            'location': location,
            'keyword': keyword or 'Any',
            'total_jobs': len(unique_jobs),
            'successful_pages': successful_pages,
            'failed_pages': failed_pages,
            'duration_seconds': round(duration, 2),
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'jobs': unique_jobs
        }
        
        if is_success:
            logger.info(f"Scraping completed: {len(unique_jobs)} unique jobs found in {duration:.2f}s")
        else:
            logger.error(f"Scraping failed: All {failed_pages} page(s) failed to fetch")
        
        return result
