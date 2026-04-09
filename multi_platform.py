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
import json
import urllib.parse
import tempfile

class JobScraper:
    def __init__(self,user_profile=False):
        # 1. Process Cleanup (Render ke liye zaroori)
        try:
            subprocess.run(['pkill', '-f', 'chrome'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass
       

        options = uc.ChromeOptions()
        options.page_load_strategy = 'eager'
        if user_profile:
            # 🔥 Wahi saved profile use karna
            # 2. PORTABLE PROFILE PATH SETUP (Current Directory)
            base_dir = os.path.dirname(os.path.abspath(__file__))
            profile_path = os.path.join(base_dir, "chrome_profile")
            options.add_argument(f"--user-data-dir={profile_path}")
            options.add_argument("--profile-directory=Default")
        else:
            # ❄️ BAKI PLATFORMS KE LIYE: Fresh/Temporary Profile
            temp_dir = tempfile.mkdtemp()
            options.add_argument(f"--user-data-dir={temp_dir}")    
    
        
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
        # options.add_argument("--disable-extensions")
        
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
            self.driver = uc.Chrome(options=options, use_subprocess=True, version_main=146)
        
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
    
    def linkedin_scrape(self, keyword, location):
        print(f"--- Scraping LinkedIn: {keyword} in {location} ---")
        jobs_data = []
        # LinkedIn Search URL format
        search_url = f"https://www.linkedin.com/jobs/search/?keywords={keyword.replace(' ', '%20')}&location={location.replace(' ', '%20')}"
        
        try:
            self.driver.get(search_url)
            time.sleep(5)

            # 1. SCROLL LOGIC (Taaki zyada jobs load ho jayein)
            for _ in range(3):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

            # 2. CARDS DETECTION
            cards = self.driver.find_elements(By.CSS_SELECTOR, ".base-card, .job-search-card")
            print(f"LinkedIn: Found {len(cards)} cards")

            for card in cards[:5]: # Batch limit
                try:
                    # Basic Info
                    title = card.find_element(By.CSS_SELECTOR, ".base-search-card__title").text.strip()
                    company = card.find_element(By.CSS_SELECTOR, ".base-search-card__subtitle").text.strip()
                    # 1. POST DATE EXTRACTION
                    try:
                        post_date = card.find_element(By.CSS_SELECTOR, "time").text.strip()
                        print(f"✅ found date in 1st : {post_date}" )
                    except:
                        try:
                            post_date = card.find_element(By.CSS_SELECTOR, ".job-search-card__listdate").text.strip()
                            print(f"✅ found date in 2nd : {post_date}" )
                        except:
                            post_date = "Recently"
                    # Click to open details
                    self.driver.execute_script("arguments[0].click();", card)
                    time.sleep(4)

                    # 3. CLEAN HTML EXTRACTION (Like Indeed/Hiring Cafe)
                    # LinkedIn ka main JD container 'details' class mein hota hai
                    # full_html = self.driver.execute_script("""
                    #     var jdContainer = document.querySelector('.details-section__content') || 
                    #                       document.querySelector('.show-more-less-html__markup') ||
                    #                       document.body;
                        
                    #     var clone = jdContainer.cloneNode(true);
                        
                    #     // Remove junk
                    #     clone.querySelectorAll('nav, footer, header, script, style, button').forEach(el => el.remove());
                        
                    #     return clone.innerHTML;
                    # """)

                    # 4. DIRECT LINK
                    link = card.find_element(By.TAG_NAME, "a").get_attribute("href").split('?')[0]

                    jobs_data.append({
                        "title": title,
                        "company": company,
                        # "description_raw": full_html.strip(), # 🔥 n8n AI ready
                        "link": link,
                        "platform": "LinkedIn",
                        "date": datetime.now().strftime("%Y-%m-%d")
                    })
                    print(f"✅ LinkedIn: {link}" )

                except Exception as e:
                    continue

        except Exception as e:
            print(f"LinkedIn Error: {e}")

        finally:
            try: self.driver.quit()
            except: pass    
        return jobs_data
    
  # --- HIRING.CAFE SCRAPER (Index Strategy - 11th Element) ---
    def hiringcafe_scrape(self, base_url, keyword="", location=""):
        print(f"--- Scraping Hiring.cafe: {base_url} ---")
        jobs_data = []
        temp_jobs = []
        try:
            self.driver.get("https://hiring.cafe/")
            
            print("Waiting 5s for UI...")
            time.sleep(5)
            
            # --- 1. KEYWORD TYPE KARO ---
            try:
                print(f"✍️ Typing Keyword: {keyword}")
                search_box = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='text']"))
                )
                search_box.click()
                time.sleep(0.5)
                search_box.send_keys(Keys.CONTROL + "a")
                search_box.send_keys(Keys.DELETE)
                search_box.send_keys(keyword)
                time.sleep(0.5)
                search_box.send_keys(Keys.ENTER)
                time.sleep(1)
            except Exception as e:
                print(f"⚠️ Keyword Error: {e}")

            # --- 2. LOCATION (CLICK 11th .w-full ELEMENT) ---
            if location:
                try:
                    print(f"📍 Interaction with Location Box: {location}")
                    
                    # Logic: User ne confirm kiya hai ki Location Box 11th element hai 'w-full' class ka.
                    # Python mein index 0 se shuru hota hai, isliye 11th = Index 10
                    
                    print("Finding all 'w-full' elements...")
                    w_full_elements = self.driver.find_elements(By.CLASS_NAME, "w-full")
                    
                    if len(w_full_elements) >= 11:
                        target_box = w_full_elements[10] # 11th Element
                        
                        print("Clicking the 11th 'w-full' element...")
                        # Scroll to view (Safe side)
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target_box)
                        time.sleep(0.5)
                        
                        # Click
                        try:
                            target_box.click()
                        except:
                            self.driver.execute_script("arguments[0].click();", target_box)
                            
                        time.sleep(2) # Modal animation waitss
                        print("Modal should be open now.")
                        # STEP: Modal ke andar ke input ko dhoondna (Using your provided ID)
                    # 1. Input box dhoondo
                    location_input = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.ID, "react-select-multi_location_selector-input"))
                    )
                    
                    def type_and_verify(text_to_type):
                        location_input.click()
                        location_input.send_keys(Keys.CONTROL + "a")
                        location_input.send_keys(Keys.DELETE)
                        
                        for char in text_to_type:
                            location_input.send_keys(char)
                            time.sleep(0.1)
                        
                        time.sleep(2) # Wait for suggestions
                        
                        # Check karo agar "No options" dikh raha hai
                        try:
                            # React-select ka default 'no options' div class ya text check
                            page_source = self.driver.page_source.lower()
                            if "no options" in page_source or "no results" in page_source:
                                return False
                            return True
                        except:
                            return True

                    # --- Execution ---
                    # Pehle Pura Address try karo
                    success = type_and_verify(location)
                    
                    if not success:
                        print(f"⚠️ Exact match fail for '{location}'. Trying fallback...")
                        # Fallback: Sirf pehla part uthao (e.g., 'TX, USA' -> 'TX')
                        fallback_loc = location.split(',')[0].strip()
                        success=type_and_verify(fallback_loc)
                        if not success:
                            fallback_loc = location.split(',')[1].strip()
                            if 'us' in fallback_loc.lower():
                                fallback_loc = "US"
                            success=type_and_verify(fallback_loc)
                           
                    
                    # Selection
                    print("Selecting top suggestion...")
                    # location_input.send_keys(Keys.ARROW_DOWN)
                    # time.sleep(0.5)
                    location_input.send_keys(Keys.ENTER)
                    time.sleep(1)
                    location_input.send_keys(Keys.ESCAPE)
                    print("Location set successfully!")
                    
                    print(f"Location '{location}' selected!")
                    
                    # 3. Final Search Trigger (Enter again or click outside)
                    time.sleep(1)
                    location_input.send_keys(Keys.ESCAPE) # Modal band karne ke liye
                    time.sleep(2)

                except Exception as e:
                    print(f"⚠️ Hiring Cafe Location Error: {e}")
                    self.driver.save_screenshot("hiring_cafe_location_fail.png")

                except Exception as e:
                    print(f"⚠️ Location Interaction Error: {e}")

            # --- 3. FETCH RESULTS ---
            print("Scrolling to load jobs...")
            self.driver.execute_script("window.scrollTo(0, 1000);")
            time.sleep(2)
            self.driver.execute_script("window.scrollTo(0, 3000);")
            time.sleep(3)

            # --- 4. DATA EXTRACTION ---
            # Job cards extraction
            job_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/viewjob/')]")
            unique_ids = set()

            for link_elem in job_links:
                try:
                    href = link_elem.get_attribute("href")
                    job_id = href.split("/viewjob/")[-1].split("?")[0]
                    if job_id in unique_ids: continue
                    
                    card = link_elem.find_element(By.XPATH, "./../../..") 
                    lines = [l.strip() for l in card.text.split('\n') if l.strip()]

                    # --- 1. FIND RAW DATE TEXT ---
                    raw_date_text = ""
                    # Card lines mein niche se dhoondo (Aksar last mein time hota hai)
                    for line in reversed(lines):
                        # Agar line mein sirf digits aur 'd','w','m','h' ho (Hiring Cafe format)
                        if re.search(r'^\d+[dwmh]$|ago', line.lower()):
                            raw_date_text = line
                            break
                    
                    # Agar upar wala fail ho, to koi bhi line jisme digit+unit ho
                    if not raw_date_text:
                        for line in lines:
                            if any(unit in line.lower() for unit in ['1d','2d','3d','4d','5d','6d','1w','2w','3w','1mo','2mo','3mo']):
                                raw_date_text = line
                                break

                    # --- 2. PARSE DATE & FILTER ---
                    parsed_date_str = self.parse_relative_date(raw_date_text)
                    job_date_obj = datetime.strptime(parsed_date_str, "%Y-%m-%d")

                    now = datetime.now()
                    two_weeks_ago = now - timedelta(days=14)
                    if job_date_obj < two_weeks_ago:
                        print(f"Skipping old job: {raw_date_text} ({parsed_date_str})")
                        continue 

                    # --- 3. DATA EXTRACTION (Sahi Sequence) ---
                    # Card ki pehli line Title hoti hai, dusri Company
                    title= lines[1] if len(lines) > 1 else "Unknown Title"
                    company =  lines[0] if len(lines) > 0 else "Unknown company"
                    

                    # Agar Title hi "1w" ya "2d" ban raha hai, toh correction logic
                    if any(x in title.lower() for x in ['1w', '2d', '1mo']):
                        # Iska matlab line sequence upar niche hai, thoda smart search karo
                        for l in lines:
                            if len(l) > 5 and not any(u in l for u in ['1d','2d','1w']):
                                title = l
                                break

                    # Location selection
                    job_loc = "Remote"
                    for line in lines:
                        if any(x in line.lower() for x in ["remote", "hybrid", "onsite", "usa", "india"]):
                            job_loc = line
                            break

                    temp_jobs.append({
                        "title": title,
                        "company": company,
                        "location": job_loc,
                        "date": parsed_date_str, # Ab ye exact YYYY-MM-DD hogi
                        "link": href,
                        "platform": "Hiring.cafe"
                    })
                    unique_ids.add(job_id)

                except Exception as e:
                    continue

            print(f"Filtered Results: Found {len(temp_jobs)} jobs from the last 2 weeks.")

            for job in temp_jobs[:5]:
                try:
                    self.driver.get(job['link'])
                    time.sleep(5) # JD load hone ka wait

                    # JavaScript to extract clean Main Content
                    clean_html = self.driver.execute_script("""
                        // 1. Hiring Cafe mein aksar 'main' tag ke andar asli content hota hai
                        var mainContent = document.querySelector('main') || 
                                        document.querySelector('.chakra-container') ||
                                        document.body;

                        var clone = mainContent.cloneNode(true);

                        // 2. Faltu elements ko remove karein (Nav, Sidebar, Footer)
                        // Hiring Cafe ke specific classes/tags
                        var unwanted = [
                            'nav', 'footer', 'header', 'script', 'style', 'iframe',
                            'svg', 'button:not([aria-label*="Apply"])', 
                            '[role="navigation"]', '.css-17849id' // Example sidebar class
                        ];
                        
                        unwanted.forEach(sel => {
                            clone.querySelectorAll(sel).forEach(el => el.remove());
                        });

                        return clone.innerHTML;
                    """)

                    jobs_data.append({
                        "title": job['title'],
                        "company": job['company'],
                        "location": job['location'],
                        "description": clean_html.strip(),
                        "date": job['date'],
                        "link": job['link'],
                        "platform": "Hiring.cafe"
                    })
                    print(f"✅ Scraped: {job['title']}")

                except Exception as e:
                    print(f"Hiring.cafe JD Error: {e}")
                    continue

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
            
            for card in cards[0:10]:
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

    def ziprecruiter_scrape(self, url, keyword="", location=""):
        print(f"--- Scraping ZipRecruiter: {url} ---")
        jobs_data = []
        try:
            self.driver.get(url)
            time.sleep(8) 

            # --- 1. POP-UP HANDLER ---
            try:
                self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                time.sleep(1)
            except: pass

            # --- 2. EXTRACT ALL JOB LINKS FIRST ---
            # Hum pehle saari details nikal lenge taaki 'Stale Element' error na aaye
            cards = self.driver.find_elements(By.CSS_SELECTOR, "article.job_result, article[id^='job-card-']")
            print(f"Total Cards Found: {len(cards)}")
            
            temp_jobs = []
            for card in cards:
                try:
                    article_id = card.get_attribute("id")
                    job_key = article_id.replace("job-card-", "") if article_id else ""
                    
                    # Direct Link Logic
                    job_link = f"https://www.ziprecruiter.com/jobs-search?{urllib.parse.urlencode({'search': keyword, 'location': location, 'lk': job_key})}"

                    # --- TARGET LINK FORMAT (Updated as per your request) ---
                    # Ye link n8n ke liye save hoga
                    final_link = f"https://www.ziprecruiter.com/jobs-search?lk={job_key}"
                    
                    title = ""
                    try: title = card.find_element(By.CSS_SELECTOR, "h2[aria-label]").get_attribute("aria-label")
                    except: title = card.find_element(By.TAG_NAME, "h2").text.strip()

                    company = "Unknown"
                    try: company = card.find_element(By.CSS_SELECTOR, "[data-testid='job-card-company']").text.strip()
                    except: pass

                    location_val = "USA"
                    try: location_val = card.find_element(By.CSS_SELECTOR, "[data-testid='job-card-location']").text.strip()
                    except: pass

                    if title and job_link:
                        temp_jobs.append({
                            "title": title,
                            "company": company,
                            "location": location_val,
                            "link": job_link,
                            "final_link": final_link
                        })
                except: continue

            
            # --- 3. VISIT EACH LINK FOR DESCRIPTION ---
            # Ab hum har link par jayenge aur JD nikalenge
            print(f"Extracting descriptions for {len(temp_jobs)} jobs...")
            for job in temp_jobs[:5]: # Starting ke 15 jobs (Safety ke liye)
                try:
                    self.driver.get(job['link'])
                    time.sleep(5) # JD load hone ka wait

                    description = ""
                    try:
                        # Aapka bataya hua specific selector
                        jd_container = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='job-details-scroll-container']"))
                        )
                        description = jd_container.text.strip()
                    except:
                        try:
                            description = self.driver.find_element(By.CLASS_NAME, "job_description").text.strip()
                        except:
                            description = "Description could not be loaded"
                    
                    # 2. ASLI APPLY LINK (External URL) - THE FIX
                        # Hum wo 'a' tag dhundenge jiska aria-label 'Apply' hai

                    try:
                            try:
                                apply_button = self.driver.find_element(By.CSS_SELECTOR, "a[aria-label='Apply']")
                                external_apply_link = apply_button.get_attribute("href")
                            except:
                                # Fallback: Agar aria-label na mile toh link jisme 'job-redirect' ho
                                apply_button = self.driver.find_element(By.XPATH, "//a[contains(@href, 'job-redirect')]")
                                external_apply_link = apply_button.get_attribute("href")  
                    except:            
                        external_apply_link = job['link'] # Default to internal link              

                    jobs_data.append({
                        "title": job['title'],
                        "company": job['company'],
                        "location": job['location'],
                        "description": description, # 🔥 Now sending to n8n
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "link": external_apply_link,
                        "platform": "ZipRecruiter"
                    })
                    print(f"✅ Scraped: {job['title']}")

                except Exception as e:
                    print(f"Error on JD page: {e}")
                    continue

        except Exception as e:
            print(f"ZipRecruiter Scraping Error: {e}")
        finally:
            try: self.driver.quit()
            except: pass
            
        return jobs_data
  # --- INDEED SCRAPER (Security & Selector Updated) ---
    def indeed_scrape(self, url):
        print(f"--- Scraping Indeed: {url} ---")
        jobs_data = []
        unique_jks = set()  # Duplicates hatane ke liye set banaya

        try:
            self.driver.get(url)
            time.sleep(15) # Security wait

            cards = self.driver.find_elements(By.CSS_SELECTOR, "div.job_seen_beacon, td.resultContent")
            temp_jobs = []
            for card in cards[0:5]:
                try:
                    # --- 1. GET UNIQUE ID (JK) FIRST ---
                    jk_id = ""
                    try:
                        jk_id = card.find_element(By.CSS_SELECTOR, "a[data-jk]").get_attribute("data-jk")
                    except:
                        continue # Agar JK hi nahi mila toh card bekar hai

                    # --- 2. DUPLICATE CHECK ---
                    if jk_id in unique_jks:
                        continue # Agar ye ID pehle aa chuki hai, toh skip karo
                    
                    # --- 3. DATA EXTRACTION ---
                    title = ""
                    try:
                        title_elem = card.find_element(By.CSS_SELECTOR, "h2.jobTitle span[title]")
                        title = title_elem.get_attribute("title")
                    except:
                        title = card.find_element(By.CSS_SELECTOR, "h2.jobTitle").text.strip()

                    try:
                        company = card.find_element(By.CSS_SELECTOR, "[data-testid='company-name']").text.strip()
                    except: company = ""

                    try:
                        location_val = card.find_element(By.CSS_SELECTOR, "[data-testid='text-location']").text.strip()
                    except: location_val = ""

                    # --- 4. CLEANING & VALIDATION ---
                    # Agar Title, Company ya Location mein se kuch bhi missing hai, toh skip karo
                    if not title or not company or not location_val:
                        print(f"Skipping incomplete job: {title}")
                        continue

                    # --- 5. FINAL ADD ---
                    temp_jobs.append({
                        "title": title,
                        "company": company,
                        "location": location_val,
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "link": f"https://www.indeed.com/viewjob?jk={jk_id}",
                        "platform": "Indeed"
                    })
                    
                    unique_jks.add(jk_id) # ID ko set mein daal do taaki dobara na aaye

                except Exception:
                    continue
            for job in temp_jobs:
                try:
                    self.driver.get(job['link'])
                    time.sleep(5) # JD load hone ka wait
                    
                    # JavaScript to extract clean HTML without Nav/Footer
                    clean_content = self.driver.execute_script("""
                        // 1. Target the main content wrapper
                        // Indeed ke naye layout mein ye container sabse best hai
                        var mainContainer = document.querySelector('.jobsearch-ViewJobLayout-jobDisplay') || 
                                        document.querySelector('.jobsearch-ViewJobLayout-content') ||
                                        document.body;

                        var clone = mainContainer.cloneNode(true);

                        // 2. Remove unnecessary elements
                        var unwanted = [
                            'nav', 'footer', 'header', 'script', 'style', 'iframe',
                            '.jobsearch-HeaderContainer', '#gnav-main-container', 
                            '.jobsearch-JobMetadataFooter', '.jobsearch-RelatedLinks'
                        ];
                        
                        unwanted.forEach(sel => {
                            clone.querySelectorAll(sel).forEach(el => el.remove());
                        });

                        return clone.innerHTML;
                    """)
                    description_html = clean_content.strip()

                    jobs_data.append({
                        "title": job['title'],  
                        "company": job['company'],
                        "location": job['location'],
                        "description": description_html,
                        "date": job['date'],
                        "link": job['link'],
                        "platform": "Indeed"
                    })
                    print(f"✅ Scraped: {job['title']}")
                except Exception as e:
                    print(f"Indeed JD Error: {e}")
                    continue        

        except Exception as e:
            print(f"Indeed Error: {e}")
        finally:
            try: self.driver.quit()
            except: pass
            
        return jobs_data
    
    def glassdoor_scrape(self, keyword, location):
        print(f"--- Scraping Glassdoor (US Base via Auto-VPN): {keyword} ---")
        jobs_data = []
        
        # Glassdoor US Search URL
        # Hum 'fromAge' parameter bhi add kar sakte hain (e.g., 7 days) filters ke liye
        search_url = f"https://www.glassdoor.com/Job/jobs.htm?sc.keyword={keyword}&locT=C&locId={location}&brandIndex=en"
        
        try:
            self.driver.get(search_url)
            # VPN ke saath initial load mein time lagta hai
            time.sleep(12)
            # 🔥 RECURSIVE RETRY LOGIC (Just a moment check)
            # current_title = self.driver.title.lower()
            # if "just a moment" in current_title or "verify you are human" in current_title:
            #     print("⚠️ Bot Detection (Just a moment) detected! Restarting...")
                
            #     # Driver close karo
            #     self.driver.quit()
                
            #     # 5 second ka break
            #     print("Waiting 5 seconds before retry...")
            #     time.sleep(5)
                
            #     # Naya driver instance create karo (JobScraper ki class se hi)
            #     # Note: Aapko ensure karna hai ki JobScraper class ka __init__ call ho sake ya naya object bane
            #     new_scraper = JobScraper(user_profile=False) # VPN profile ke saath
            #     return new_scraper.glassdoor_scrape(keyword, location) 

            # 1. CARDS DETECTION (Based on your HTML file)
            # Glassdoor aksar 'jobCard' ya 'react-job-listing' use karta hai
            cards = self.driver.find_elements(By.CLASS_NAME, "jobCard")
            print(f"Glassdoor: Found {len(cards)} job cards.")
            temp_jobs = []
            for card in cards[:5]: # Batch limit for n8n efficiency

                try:
                    print(card.text)
                    # Title & Company extraction
                    title = card.text.split('\n')[2].strip()
                    try:
                        company = card.text.split('\n')[0].strip()
                    except:
                         company="Unknown Company" 
                    print(f"Extracting job: {title} at {company}")     
                    # 2. CLICK TO LOAD DESCRIPTION
                    # Click se right side panel mein JD load hota hai
                    self.driver.execute_script("arguments[0].click();", card)
                    time.sleep(4)

                    try:
                        # Title wale anchor tag ko target karo jo clean link rakhta hai
                        title_element = card.find_element(By.CSS_SELECTOR, 'a[data-test="job-title"]')
                        job_link = title_element.get_attribute('href')
                        
                        # Example clean link: https://www.glassdoor.com/job-listing/...
                        print(f"✅ Clean Job URL: {job_link}")

                    except Exception as e:
                        print(f"❌ Error getting clean link: {e}")
                        job_link = "Link Not Found"

                    # 3. CLEAN TEXT DESCRIPTION (No HTML as requested)
                    # Selector updated based on Glassdoor's standard React container
            
                    try:
                        posted_at = card.text.split('\n')[-1].strip()
                        posted_at = self.parse_relative_date(posted_at)
                    except:
                        posted_at = datetime.now().strftime("%Y-%m-%d")   

                    temp_jobs.append({
                        "title": title,

                        "company": company,
                        "posted_at": posted_at,
                        "link": job_link,
                    })
                    # print(f"✅ Glassdoor: {jobs_data} ")

                except Exception as e:
                    continue
            for job in temp_jobs:
                try:
                    self.driver.get(job['link'])
                    time.sleep(5) # JD load hone ka wait

                    # # JavaScript to extract clean Main Content
                    # clean_text = self.driver.execute_script("""
                    #     // 1. Target the main job description container
                    #     var jdContainer = document.querySelector('.jobDescriptionContent') || 
                    #                     document.querySelector('.jobDescription') ||
                    #                     document.body;

                    #     return jdContainer.inne
                    description_section = self.driver.find_element(By.CSS_SELECTOR, ".JobDetails_jobDescription__uW_fK").text.strip()

                    jobs_data.append({
                        "title": job['title'],
                        "company": job['company'],
                        "description": description_section,
                        "date": job['posted_at'],
                        "link": job['link'],
                        "platform": "Glassdoor"
                    })
                    print(f"✅ Scraped: {job['title']}")

                except Exception as e:
                    print(f"Glassdoor JD Error: {e}")
                    continue

        except Exception as e:
            print(f"Glassdoor Main Error: {e}")
        finally:
            try: self.driver.quit()
            except: pass    
        return jobs_data
    
    def simplyhired_scrape(self, keyword, location):
        print(f"--- Scraping SimplyHired: {keyword} in {location} ---")
        jobs_data = []
        search_url = f"https://www.simplyhired.com/search?q={keyword.replace(' ', '+')}&l={location.replace(' ', '+')}"
        
        try:
            self.driver.get(search_url)
            time.sleep(8) # Chakra UI load hone ka wait

            # 1. FIXED CARDS DETECTION (Using li.css-0 and data-testid)
            # Aapki file ke mutabiq search results 'li.css-0' mein hote hain
            titles = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='searchSerpJobTitle']")
            cards = []
            for t in titles:
                try:
                    cards.append(t.find_element(By.XPATH, "./ancestor::li[1]"))
                except: continue

            print(f"SimplyHired: Found {len(cards)} cards")
            
            for card in cards[:5]:
                try:
                    # --- BASIC INFO ---
                    title_el = card.find_element(By.CSS_SELECTOR, "[data-testid='searchSerpJobTitle'] a")
                    title = title_el.text.strip()
                    job_link = title_el.get_attribute("href")
                    company = card.find_element(By.CSS_SELECTOR, "[data-testid='companyName']").text.strip()

                    # --- LOCATION EXTRACTION (Robust Logic) ---
                    try:
                        location_text = card.find_element(By.CSS_SELECTOR, "[data-testid='searchSerpJobLocation']").text.strip()
                    except:
                        try:
                            # Fallback: Split by dash from card text (e.g., Company — Location)
                            full_text = card.text
                            location_text = full_text.split("—")[1].split("\n")[0].strip() if "—" in full_text else "USA"
                        except:
                            location_text = "United States"

                    # --- DATE EXTRACTION ---
                    try:
                        date_raw = card.find_element(By.CSS_SELECTOR, "[data-testid='searchSerpJobDateStamp']").text.strip()
                        date_text = self.parse_relative_date(date_raw) # Aapka custom parser
                    except:
                        date_text = datetime.now().strftime("%Y-%m-%d")

                    # --- 🚀 GET FULL JOB DETAILS (HTML + TEXT) ---
                    # Click card to load the side panel
                    self.driver.execute_script("arguments[0].click();", title_el)
                    time.sleep(4)

                    # Targetting the main container from your detail page file
                    description_container = self.driver.find_element(By.CSS_SELECTOR, "div[data-testid='viewJobBodyJobFullDescriptionContent']")
                    
                    # Full HTML for n8n AI parsing if needed
                    description_html = description_container.get_attribute('innerHTML')
                    # Clean text for simple analysis
                    description_clean = description_container.text.strip()

                    jobs_data.append({
                        "title": title,
                        "company": company,
                        "location": location_text,
                        "posted_at": date_text,
                        "link": job_link,
                        "description_text": description_clean,
                        "platform": "SimplyHired"
                    })
                    print(f"✅ Extracted SimplyHired: {title} at {company}")

                except Exception as e:
                    print(f"Card Error: {e}")
                    continue

        except Exception as e:
            print(f"SimplyHired Main Error: {e}")

        finally:
            try: self.driver.quit()
            except: pass      
            
        return jobs_data
        
    def builtin_scrape(self, keyword, location):
        print(f"--- Scraping BuiltIn: {keyword} in {location} ---")
        jobs_data = []
        
        # BuiltIn URL structure: Keyword aur Location dono ko query mein pass kar rahe hain
        # 'allLocations=true' se ye pure location radius ko search karta hai
        search_url = f"https://builtin.com/jobs?search={keyword.replace(' ', '+')}&location={location.replace(' ', '+')}&allLocations=true"
        
        try:
            self.driver.get(search_url)
            time.sleep(8) # Chakra/BuiltIn UI load hone ka wait

            # 1. CARDS EXTRACTION (Using data-id from your snippet)
            # Aapki file mein main container div[data-id="job-card"] hai
            cards = self.driver.find_elements(By.CSS_SELECTOR, "div[data-id='job-card']")
            
            # Fallback agar data-id na mile
            if not cards:
                cards = self.driver.find_elements(By.CSS_SELECTOR, ".job-bounded-responsive")

            print(f"BuiltIn: Found {len(cards)} cards for location: {location}")

            for card in cards[:5]:
                try:
                    # --- Title & Direct Link ---
                    # Selector: data-id="job-card-title"
                    title_el = card.find_element(By.CSS_SELECTOR, "a[data-id='job-card-title']")
                    title = title_el.text.strip()
                    job_link = title_el.get_attribute("href")
                    
                    # --- Company ---
                    # Selector: data-id="company-title"
                    company = card.find_element(By.CSS_SELECTOR, "a[data-id='company-title']").text.strip()
                    
                    # --- Location Extraction ---
                    # Aapke snippet mein location span.font-barlow ke andar hai
                    try:
                        loc_elements = card.find_elements(By.CSS_SELECTOR, "span.font-barlow")
                        # Usually 2nd or 3rd span location hota hai
                        job_loc = loc_elements[-1].text.strip() if loc_elements else location
                    except:
                        job_loc = location

                    # --- Date (Posted) ---
                    # Selector: span.bg-gray-01 (e.g., "Reposted 4 Days Ago")
                    try:
                        date_text = card.find_element(By.CSS_SELECTOR, "span.bg-gray-01").text.replace("Reposted", "").strip()
                        date_text = self.parse_relative_date(date_text)
                    except:
                        date_text = datetime.now().strftime("%Y-%m-%d")

                    # --- 🚀 FULL DESCRIPTION EXTRACTION (New Tab) ---
                    main_window = self.driver.current_window_handle
                    self.driver.execute_script(f"window.open('{job_link}', '_blank');")
                    time.sleep(5) # Job page load hone ka wait
                    
                    self.driver.switch_to.window(self.driver.window_handles[1])
                    
                    try:
                        # BuiltIn job description page selector
                        desc_el = self.driver.find_element(By.CSS_SELECTOR, ".job-description")
                        full_html = desc_el.get_attribute('innerHTML')
                        full_text = desc_el.text.strip()
                    except:
                        full_html = full_text = "Description container not found"

                    # Tab band karke wapas aao
                    self.driver.close()
                    self.driver.switch_to.window(main_window)

                    jobs_data.append({
                        "title": title,
                        "company": company,
                        "location": job_loc,
                        "posted_at": date_text,
                        # "description_html": full_html,
                        "description_text": full_text,
                        "link": job_link,
                        "platform": "BuiltIn"
                    })
                    print(f"✅ Scraped BuiltIn: {title} | {job_loc}")

                except Exception as e:
                    # Error aane par ensure karein ki main window par hi hain
                    if len(self.driver.window_handles) > 1:
                        self.driver.close()
                        self.driver.switch_to.window(main_window)
                    continue

        except Exception as e:
            print(f"BuiltIn Main Error: {e}")
        finally:
            try: self.driver.quit()
            except: pass    
        return jobs_data
    
    def careerbuilder_scrape(self, keyword, location):
        print(f"--- Scraping CareerBuilder: {keyword} in {location} ---")
        jobs_data = []
        
        # CareerBuilder URL structure
        search_url = f"https://www.careerbuilder.com/jobs?keywords={keyword.replace(' ', '+')}&location={location.replace(' ', '+')}"
        
        try:
            self.driver.get(search_url)
            time.sleep(6) # Initial load wait

            # 1. CARDS EXTRACTION
            # CareerBuilder cards usually have a 'job-listing-item' class
            cards = self.driver.find_elements(By.CSS_SELECTOR, ".job-listing-item")
            
            if not cards:
                # Fallback selector
                cards = self.driver.find_elements(By.CSS_SELECTOR, "li.item")

            print(f"CareerBuilder: Found {len(cards)} cards")

            for card in cards[:5]:
                try:
                    # --- Title & Direct Link ---
                    title_el = card.find_element(By.CSS_SELECTOR, "h2.job-title a")
                    title = title_el.text.strip()
                    job_link = title_el.get_attribute("href")
                    
                    # --- Company & Location ---
                    try:
                        company = card.find_element(By.CSS_SELECTOR, ".company-name").text.strip()
                    except: company = "N/A"
                    
                    try:
                        loc = card.find_element(By.CSS_SELECTOR, ".job-location").text.strip()
                    except: loc = location

                    # --- Date ---
                    try:
                        date_text = card.find_element(By.CSS_SELECTOR, ".job-post-date").text.strip()
                    except: date_text = "Recently"

                    # --- 🚀 FULL DESCRIPTION EXTRACTION (Navigating to Link) ---
                    # CareerBuilder par hum seedha link par ja sakte hain
                    main_window = self.driver.current_window_handle
                    self.driver.execute_script(f"window.open('{job_link}', '_blank');")
                    time.sleep(5)
                    self.driver.switch_to.window(self.driver.window_handles[1])
                    
                    try:
                        # CareerBuilder description selector
                        desc_el = self.driver.find_element(By.ID, "job-description")
                        if not desc_el:
                            desc_el = self.driver.find_element(By.CLASS_NAME, "jdp-description-details")
                            
                        full_html = desc_el.get_attribute('innerHTML')
                        full_text = desc_el.text.strip()
                    except:
                        full_html = full_text = "Description not found"

                    self.driver.close()
                    self.driver.switch_to.window(main_window)

                    jobs_data.append({
                        "title": title,
                        "company": company,
                        "location": loc,
                        "posted_at": date_text,
                        "description_html": full_html,
                        "description_text": full_text,
                        "link": job_link,
                        "platform": "CareerBuilder"
                    })
                    print(f"✅ CareerBuilder: {title} | {company}")

                except Exception as e:
                    if len(self.driver.window_handles) > 1:
                        self.driver.close()
                        self.driver.switch_to.window(main_window)
                    continue

        except Exception as e:
            print(f"CareerBuilder Main Error: {e}")
            
        return jobs_data
# --- MAIN EXECUTION ---
if __name__ == "__main__":
    bot = JobScraper()
    
    # Example: Dice.com - Uses React/JavaScript to load jobs dynamically
    indeed_jobs = bot.dice_scrape(url="https://www.dice.com/jobs?q=ai+agetn+developer&location=surat",)
    print(indeed_jobs)    
