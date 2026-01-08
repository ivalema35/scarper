import requests
from bs4 import BeautifulSoup
import time

# Target URL (Freelancer Search Page)
url = "https://www.freelancer.in/jobs/n8n/"

def fetch_gigs():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Job Cards dhundo (Inspect Element karke class name check karna padega)
        jobs = soup.find_all('div', class_='JobSearchCard-item')
        
        for job in jobs:
            try:
                title = job.find('a', class_='JobSearchCard-primary-heading-link').text.strip()
                price = job.find('div', class_='JobSearchCard-primary-price').text.strip()
                link = "https://www.freelancer.in" + job.find('a', class_='JobSearchCard-primary-heading-link')['href']
            
                print(f"🔥 Gig Found: {title}")
                print(f"💰 Price: {price}")
                print(f"🔗 Link: {link}")
                print("-" * 30)
            except Exception as e:
                print(f"Error parsing job: {e}")
    else:
        print("Failed to fetch data")

# Script Run
fetch_gigs()