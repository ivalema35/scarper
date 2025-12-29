from requests import options
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import random
from datetime import datetime, timedelta
import re
import os
import subprocess
import platform

class JobScraper:
    def __init__(self):
        # 1. Process Cleanup (Render ke liye zaroori)
        try:
            subprocess.run(['pkill', '-f', 'chrome'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass
            
        options = uc.ChromeOptions()
        options.page_load_strategy = 'normal'
        
        # --- 1. STRICT LINUX AGENT FOR RENDER ---
        # User-Agent rotation hata kar ek solid Linux agent use kar rahe hain
        if platform.system() == "Windows":
             options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
        else:
             # Render ke liye yahi best hai
             options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")

        # --- 2. STEALTH ARGUMENTS (Sabse Zaroori) ---
        # options.add_argument('--headless=new')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--start-maximized')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        
        # Hide Automation signals
        options.add_argument('--disable-blink-features=AutomationControlled') 
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-extensions")
        
        # Advanced Stealth (Ye flag pakde jane se bachat hai)
        # options.add_experimental_option("excludeSwitches", ["enable-automation"])
        # options.add_experimental_option('useAutomationExtension', False)
        
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values.notifications": 2,
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "intl.accept_languages": "en-US,en"
        }
        options.add_experimental_option("prefs", prefs)

        # --- RENDER PATH ---
        base_path = "/opt/render/project/.render/chrome"
        
        if os.path.exists(base_path):
            print("--- Running on Render Server ---")
            chrome_binary = os.path.join(base_path, "opt/google/chrome/google-chrome")
            driver_binary = os.path.join(base_path, "chromedriver")
            if os.path.exists(chrome_binary): options.binary_location = chrome_binary
            
            self.driver = uc.Chrome(
                options=options, 
                driver_executable_path=driver_binary, 
                version_main=131
            )
        else:
            print("--- Running Local ---")
            self.driver = uc.Chrome(options=options, use_subprocess=True)
        
        # --- 3. JAVASCRIPT INJECTION (Navigator Override) ---
        # Browser ko jhoot bolne par majboor karna ki wo automate nahi ho raha
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """
        })
            
        self.driver.set_window_size(1920, 1080)



    def parse_relative_date(self, date_text):
        """
        Converts '7d ago', 'Yesterday', 'Today' into '2024-05-20' format.
        """
        if not date_text:
            return datetime.now().strftime("%Y-%m-%d")
        
        text = date_text.lower().strip()
        current_date = datetime.now()

        try:
            # Case 1: "Today", "Just now", "Hours ago" -> Aaj ki date
            if any(x in text for x in ["today", "just", "now", "hour", "h "]):
                return current_date.strftime("%Y-%m-%d")

            # Case 2: "Yesterday" -> Kal ki date
            elif "yesterday" in text:
                return (current_date - timedelta(days=1)).strftime("%Y-%m-%d")

            # Case 3: "7d ago" ya "7 days ago" -> Subtract Days
            elif "d" in text or "day" in text:
                # Sirf number nikalo (regex se)
                match = re.search(r'(\d+)', text)
                if match:
                    days_ago = int(match.group(1))
                    new_date = current_date - timedelta(days=days_ago)
                    return new_date.strftime("%Y-%m-%d")

            # Case 4: "2w ago" ya "2 weeks ago" -> Subtract Weeks
            elif "w" in text or "week" in text:
                match = re.search(r'(\d+)', text)
                if match:
                    weeks_ago = int(match.group(1))
                    new_date = current_date - timedelta(weeks=weeks_ago)
                    return new_date.strftime("%Y-%m-%d")
            
            # Case 5: "1m ago" (Month) -> Approx 30 days minus
            elif "m" in text or "mon" in text:
                match = re.search(r'(\d+)', text)
                if match:
                    months_ago = int(match.group(1))
                    new_date = current_date - timedelta(days=months_ago * 30)
                    return new_date.strftime("%Y-%m-%d")

        except Exception:
            pass # Agar koi error aaye to original text hi return kar do ya aaj ki date

        # Agar format samajh nahi aaya, to wahi text wapas bhej do (debugging ke liye)
        return current_date.strftime("%Y-%m-%d")

   # --- HIRING.CAFE SCRAPER (Interaction Mode) ---
    def hiringcafe_scrape(self, url, keyword="", location=""):
        print(f"--- Scraping Hiring.cafe: {url} ---")
        jobs_data = []
        try:
            self.driver.get("https://hiring.cafe/") # Base URL open karein
            
            print("Waiting for UI to load...")
            time.sleep(5)
            
            # --- INTERACTION: TYPE KEYWORD ---
            try:
                print(f"Typing Keyword: {keyword}")
                # Search input dhundo (Placeholder ya ID se)
                search_box = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='Search'], input[id*='search']"))
                )
                search_box.click()
                # Purana text saaf karo (Ctrl+A -> Delete reliable hota hai React me)
                search_box.send_keys(Keys.CONTROL + "a")
                search_box.send_keys(Keys.DELETE)
                # Keyword type karo
                search_box.send_keys(keyword)
                time.sleep(1)
                search_box.send_keys(Keys.ENTER)
                time.sleep(3)
            except Exception as e:
                print(f"Search Box Error: {e}")

            # --- INTERACTION: TYPE LOCATION ---
            # Location box thoda tricky ho sakta hai, try karte hain
            if location:
                try:
                    print(f"Typing Location: {location}")
                    # Location input dhundne ki koshish (Placeholder ya common attributes)
                    loc_box = self.driver.find_element(By.CSS_SELECTOR, "input[placeholder*='Location'], input[placeholder*='City'], input[placeholder*='Remote']")
                    
                    loc_box.click()
                    loc_box.send_keys(Keys.CONTROL + "a")
                    loc_box.send_keys(Keys.DELETE)
                    loc_box.send_keys(location)
                    time.sleep(1)
                    loc_box.send_keys(Keys.ENTER)
                    time.sleep(4) # Results update hone ka wait
                except:
                    print("Location box not found or hard to interact, scraping mixed results...")

            # --- MASTER STRATEGY: Find Links with '/viewjob/' ---
            # Ab job results load ho chuke honge
            self.driver.execute_script("window.scrollTo(0, 1000);")
            time.sleep(3)
            self.driver.execute_script("window.scrollTo(0, 3000);")
            time.sleep(3)
            
            job_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/viewjob/')]")
            print(f"Found {len(job_links)} valid job links.")
            
            unique_ids = set()

            for link_elem in job_links:
                try:
                    href = link_elem.get_attribute("href")
                    job_id = href.split("/viewjob/")[-1].split("?")[0]
                    
                    if job_id in unique_ids: continue
                    unique_ids.add(job_id)

                    # Card Text Extraction (Parent Methsod)
                    card = link_elem.find_element(By.XPATH, "./../../..") 
                    text = card.text.strip()
                    lines = [line.strip() for line in text.split('\n') if line.strip()]

                    if len(lines) < 2:
                        title = link_elem.text.strip()
                        company = "Hiring.cafe Job"
                    else:
                        title = lines[0]
                        company = "Unknown"
                        if len(lines) > 1:
                            if "$" not in lines[1] and "Remote" not in lines[1]:
                                company = lines[1]
                        
                        location_text = "Remote"
                        for line in lines:
                            if any(x in line.lower() for x in ["remote", "india", "usa", "hybrid", "onsite"]):
                                location_text = line
                                break

                    posted_date = datetime.now().strftime("%Y-%m-%d")

                    jobs_data.append({
                        "title": title,
                        "company": company,
                        "location": location_text,
                        "date": posted_date,
                        "link": href,
                        "platform": "Hiring.cafe"
                    })
                except: continue

        except Exception as e:
            print(f"Hiring.cafe Error: {e}")
        finally:
            try: self.driver.quit()
            except: pass
            
        return jobs_data
    
    def dice_scrape(self, url, ):
        # print(f"--- Scraping {platform_name} ---")
        self.driver.get(url)
        time.sleep(5)
        card_selector="[data-testid='job-card']"    # Custom web component
        title_selector="[data-testid='job-search-job-detail-link']"     # Job title link with ID starting with position-title
        link_selector="[data-testid='job-search-job-card-link']"       # Same element for link
        
        # Human behavior mimic karne ke liye random sleep
        # time.sleep(random.uniform(8, 12))
        
        # Multiple scrolls for dynamic content loading
        for i in range(3):
            self.driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight/{3-i});")
            time.sleep(1)

        jobs_data = []
        
        try:
            # Try multiple selector strategies
            selectors_to_try = [
                card_selector,  # Original selector
                "div[data-testid='search-result-card']",
                "dhi-js-search-result-card",
                "div.card",
                "article",
                "[class*='card']"
            ]
            
            cards = []
            for selector in selectors_to_try:
                try:
                    print(f"Trying selector: {selector}")
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if cards:
                        print(f"✓ Found {len(cards)} cards with selector: {selector}")
                        break
                except:
                    continue
            
            if not cards:
                print("❌ No cards found with any selector. Trying generic approach...")
                # Last resort: find all links and filter
                all_links = self.driver.find_elements(By.TAG_NAME, "a")
                print(f"Found {len(all_links)} total links on page")
            
            for card in cards:
                try:
                    title = card.find_element(By.CSS_SELECTOR, title_selector).text
                    print(f"Extracting job: {title}")
                    # Link nikalne ke liye check (kabhi href parent pe hota hai, kabhi child pe)
                    try:
                        link_elem = card.find_element(By.CSS_SELECTOR, link_selector)
                        link = link_elem.get_attribute('href')
                    except:
                        # Agar direct link selector kaam na kare to poore card ka href try karein
                        link = card.get_attribute('href')
                    meta_elements = card.find_elements(By.CSS_SELECTOR, "p.text-sm.font-normal.text-zinc-600")
                    print(f"Found {len(meta_elements)} meta elements")
                    
                    try:
                        location = meta_elements[0].text
                    except Exception as e:
                        location = f"Location Not Found {e}"

                    # 4. Posted Date (New)
                    try:
                        posted_date = self.parse_relative_date(meta_elements[-1].text)
                    except Exception as e:
                        posted_date = f"Date Not Found {e}"

                    if title:
                        job_info = {
                        "Title": title,
                        "Location": location,
                        "Date": posted_date,
                        "Link": link
                    }
                        jobs_data.append(job_info)
                        print(f"Scraped: {title} | {location} | {posted_date}")
                       

                        
                except Exception as e:
                    continue # Agar ek card fail ho jaye to agle pe jao

        except Exception as e:
            print(f"Error on dice jobs : {e}")
            
        finally:
            # --- YEH LINE BAHUT ZAROORI HAI ---
            try:
                self.driver.quit()
            except:
                pass    
            
        return jobs_data

    # --- ZIPRECRUITER SCRAPER (NEW) ---
    def ziprecruiter_scrape(self, url):
        print(f"--- Scraping ZipRecruiter: {url} ---")
        jobs_data = []
        try:
            self.driver.get(url)
            
            # --- CLOUDFLARE BYPASS LOGIC ---
            print("Checking for Cloudflare Challenge...")
            time.sleep(12) # 12 seconds wait zaroori hai challenge ke liye
            
            # Debug Title
            title = self.driver.title
            print(f"DEBUG: Current Page Title -> {title}")
            
            if "Just a moment" in title or "Verifying" in title:
                print("⚠️ Cloudflare Detected! Simulating Human Behavior...")
                
                # FIX: Python ka random number pehle calculate karo, fir JS ko bhejo
                random_scroll = random.randint(200, 600)
                self.driver.execute_script(f"window.scrollTo(0, {random_scroll});")
                time.sleep(5)
                
                # Check again
                if "Just a moment" in self.driver.title:
                    print("Still stuck. Sending a Refresh...")
                    self.driver.refresh()
                    time.sleep(15)

            # Slow scroll to trigger lazy loading
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 3);")
            time.sleep(3)

            # Cards Extraction
            cards = self.driver.find_elements(By.CSS_SELECTOR, "li.job-listing")
            
            if len(cards) == 0:
                print("⚠️ 0 Jobs. Saving screenshot for IV Infotech debugging...")
                self.driver.save_screenshot("zip_cloudflare_local.png")
            
            print(f"Total Cards Found: {len(cards)}")

            for card in cards:
                try:
                    title_elem = card.find_element(By.CSS_SELECTOR, "a.jobList-title")
                    title = title_elem.text.strip()
                    link = title_elem.get_attribute("href")

                    meta_items = card.find_elements(By.CSS_SELECTOR, "ul.jobList-introMeta li")
                    company = meta_items[0].text.strip() if len(meta_items) > 0 else "Unknown"
                    location = meta_items[1].text.strip() if len(meta_items) > 1 else "Unknown"

                    try:
                        date_text = card.find_element(By.CSS_SELECTOR, "div.jobList-date").text.strip()
                        posted_date = self.parse_relative_date(date_text)
                    except: 
                        posted_date = datetime.now().strftime("%Y-%m-%d")

                    jobs_data.append({
                        "title": title, "company": company, "location": location, 
                        "date": posted_date, "link": link, "platform": "ZipRecruiter"
                    })
                except: continue

        except Exception as e:
            print(f"ZipRecruiter Error: {e}")
        finally:
            try: self.driver.quit()
            except: pass
            
        return jobs_data
    
    # --- INDEED SCRAPER (Improved) ---
    def indeed_scrape(self, url):
        print(f"--- Scraping Indeed: {url} ---")
        jobs_data = []
        try:
            # 1. Clean Slate
            self.driver.delete_all_cookies()
            self.driver.get(url)
            
            # 2. Wait for Cloudflare Check
            print("Waiting 15s for Cloudflare/Page Load...")
            time.sleep(15)
            
            # 3. Check if Blocked
            title = self.driver.title
            print(f"DEBUG: Initial Title -> {title}")
            
            if "Blocked" in title or "Just a moment" in title or "Access denied" in title:
                print("⚠️ Block Detected! Attempting Bypass...")
                
                # Action 1: Mouse Move
                self.driver.execute_script("window.scrollTo(0, 500);")
                time.sleep(2)
                
                # Action 2: Hard Refresh
                self.driver.refresh()
                print("Refreshed. Waiting 20s...")
                time.sleep(20) # Cloudflare solve hone ka time do
                
                print(f"DEBUG: New Title -> {self.driver.title}")

            # 4. Scroll to trigger lazy load
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
            time.sleep(2)

            # 2. CHECK FOR CARDS
            cards = self.driver.find_elements(By.CSS_SELECTOR, "div.job_seen_beacon")
            
            # 3. RETRY LOGIC (Agar 0 jobs mili)
            if len(cards) == 0:
                print("⚠️ 0 Jobs Found. Retrying with explicit wait...")
                try:
                    WebDriverWait(self.driver, 20).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "resultContent"))
                    )
                    cards = self.driver.find_elements(By.CSS_SELECTOR, "div.job_seen_beacon")
                except:
                    # Agar fir bhi nahi mila, to HTML check karein
                    print("❌ Still 0 jobs. Dumping Page Source (First 500 chars):")
                    print(self.driver.page_source[:500]) # Ye logs mein dikhega ki kya error hai
            
            print(f"Total Cards Found: {len(cards)}")

            for card in cards:
                try:
                    # Extraction Logic
                    title_elem = card.find_element(By.CSS_SELECTOR, "h2.jobTitle span[title]")
                    title = title_elem.get_attribute("title")
                    
                    try: company = card.find_element(By.CSS_SELECTOR, "[data-testid='company-name']").text
                    except: company = "Unknown"

                    try: location = card.find_element(By.CSS_SELECTOR, "[data-testid='text-location']").text
                    except: location = "Unknown"

                    try: 
                        date_text = card.find_element(By.CSS_SELECTOR, "[data-testid='myJobsStateDate']").text
                        posted_date = self.parse_relative_date(date_text)
                    except: posted_date = datetime.now().strftime("%Y-%m-%d")

                    # Link
                    try:
                        link_elem = card.find_element(By.CSS_SELECTOR, "h2.jobTitle a")
                        raw_link = link_elem.get_attribute("href")
                        jk_match = re.search(r"jk=([a-zA-Z0-9]+)", raw_link)
                        link = f"https://www.indeed.com/viewjob?jk={jk_match.group(1)}" if jk_match else raw_link
                    except: link = url

                    jobs_data.append({
                        "title": title, "company": company, "location": location, 
                        "date": posted_date, "link": link, "platform": "Indeed"
                    })

                except Exception as e:
                    continue

        except Exception as e:
            print(f"Indeed Error: {e}")
        
        finally:
            try: self.driver.quit()
            except: pass
            
        return jobs_data
   
# --- MAIN EXECUTION ---
if __name__ == "__main__":
    bot = JobScraper()
    
    # Example: Dice.com - Uses React/JavaScript to load jobs dynamically
    indeed_jobs = bot.dice_scrape(url="https://www.dice.com/jobs?q=ai+agetn+developer&location=surat",)
    print(indeed_jobs)    
#         location_selector="[data-testid='search-result-location']",
#         posted_date_selector="[data-testid='search-result-posted-date']"
#     )
#     dice_jobs_count = len(dice_jobs)
#     print(dice_jobs)
#     print(f"Total jobs found on Dice: {dice_jobs_count}")
#     with open("dice_jobs.txt", "w", encoding="utf-8") as f:
#         for job in dice_jobs:
#             f.write(f"{job['Title']} - {job['Link']}\n")
#     # Example: Glassdoor (Bahut strict hai, login maang sakta hai)
#     # glassdoor_jobs = bot.scrape_platform(
#     #     platform_name="Glassdoor",
#     #     url="https://www.glassdoor.co.in/Job/software-tester-jobs-SRCH_KO0,15.htm",
#     #     card_selector="li.react-job-listing", # Glassdoor list item
#     #     title_selector="div.job-title",       # Job Title class
#     #     link_selector="a.job-link"            # Link class
#     # )

#     bot.close()
#     print("Scraping Completed")