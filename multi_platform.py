from requests import options
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
from datetime import datetime, timedelta
import re
import os
import subprocess

class JobScraper:
    def __init__(self):
        options = uc.ChromeOptions()
       # --- SPEED BOOSTERS (Ye zaroori hai) ---
        
        # 1. Page Load Strategy 'eager': 
        # Yeh Chrome ko bolta hai: "HTML mil gaya? Bas kaafi hai. Images ka wait mat karo."
        # Isse 60 second ka kaam 10 second mein ho jata hai.
        options.page_load_strategy = 'eager' 
        
        # 2. Block Images & Heavy Assets
        # Images load karne mein RAM aur Data waste hota hai.
        prefs = {
            "profile.managed_default_content_settings.images": 2, # Block Images
            "profile.default_content_setting_values.notifications": 2, # Block Notifications
        }
        options.add_experimental_option("prefs", prefs)
        
        # Standard Headless Options
        # options.add_argument('--headless=new')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--dns-prefetch-disable') # Network speedup

        # --- PATH SETUP (Render wala code same rahega) ---
        base_path = "/opt/render/project/.render/chrome"
        chrome_binary = os.path.join(base_path, "opt/google/chrome/google-chrome")
        driver_binary = os.path.join(base_path, "chromedriver")

        if os.path.exists(chrome_binary):
            options.binary_location = chrome_binary

        if os.path.exists(driver_binary):
            print("Using Custom Driver Path on Render")
            self.driver = uc.Chrome(
                options=options, 
                driver_executable_path=driver_binary, 
                version_main=131
            )
        else:
            print("Using Default Local Driver")
            self.driver = uc.Chrome(options=options)



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

    def indeed_scrape(self, url):
        print(f"--- Scraping Indeed: {url} ---")
        jobs_data = []
        try:
            self.driver.get(url)
            time.sleep(5) # Eager load wait

            # 1. Close Popup if exists (Indeed Google Login Popup)
            try:
                close_btn = self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='close']")
                close_btn.click()
                print("Popup closed")
                time.sleep(1)
            except:
                pass

            # 2. Wait for Job Cards
            # Aapki file mein 'td.resultContent' main content holder hai
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, "resultContent"))
            )
            
            # Cards Selectors (Based on your HTML file)
            # Indeed structure: li > div.cardOutline > div.job_seen_beacon
            cards = self.driver.find_elements(By.CSS_SELECTOR, "div.job_seen_beacon")
            print(f"Total Cards Found: {len(cards)}")

            for card in cards:
                try:
                    # Title
                    # HTML: <h2 class="jobTitle"><span>Python Dev</span></h2>
                    title_elem = card.find_element(By.CSS_SELECTOR, "h2.jobTitle span[title]")
                    title = title_elem.get_attribute("title")

                    # Company
                    # HTML: <span data-testid="company-name">Google</span>
                    try:
                        company = card.find_element(By.CSS_SELECTOR, "[data-testid='company-name']").text
                    except:
                        company = "Unknown"

                    # Location
                    # HTML: <div data-testid="text-location">Remote</div>
                    try:
                        location = card.find_element(By.CSS_SELECTOR, "[data-testid='text-location']").text
                    except:
                        location = "Unknown"

                    # Date
                    # HTML: <span data-testid="myJobsStateDate">Posted 3 days ago</span>
                    try:
                        date_text = card.find_element(By.CSS_SELECTOR, "[data-testid='myJobsStateDate']").text
                        posted_date = self.parse_relative_date(date_text)
                    except:
                        posted_date = datetime.now().strftime("%Y-%m-%d")

                    # Link
                    try:
                        link_elem = card.find_element(By.CSS_SELECTOR, "h2.jobTitle a")
                        raw_link = link_elem.get_attribute("href")
                        
                        # Regex se 'jk' (Job Key) nikalenge
                        # Pattern: jk= ke baad aane wale numbers/letters
                        jk_match = re.search(r"jk=([a-zA-Z0-9]+)", raw_link)
                        
                        if jk_match:
                            job_key = jk_match.group(1)
                            # Clean Direct Link
                            link = f"https://www.indeed.com/viewjob?jk={job_key}"
                        else:
                            # Agar jk nahi mila to fallback
                            if raw_link.startswith("/"):
                                link = f"https://www.indeed.com{raw_link}"
                            else:
                                link = raw_link
                                
                    except Exception as e:
                        link = url # Fallback to search page

                    # Data Store
                    job = {
                        "title": title,
                        "company": company,
                        "location": location,
                        "date": posted_date,
                        "link": link,
                        "platform": "Indeed"
                    }
                    jobs_data.append(job)
                    print(f"Scraped: {title} | {company}")

                except Exception as e:
                    continue

        except Exception as e:
            print(f"Indeed Error: {e}")
        
        finally:
            try:
                self.driver.quit()
            except:
                pass
            
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