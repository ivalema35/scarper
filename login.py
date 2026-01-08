import undetected_chromedriver as uc
import os
import time

def create_job_profile():
    # 1. Path setup (Usi folder mein jahan script hai)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    profile_path = os.path.join(base_dir, "chrome_profile")
    
    if not os.path.exists(profile_path):
        os.makedirs(profile_path)
    
    print(f"--- Creating Profile at: {profile_path} ---")
    
    options = uc.ChromeOptions()
    options.add_argument(f"--user-data-dir={profile_path}")
    options.add_argument("--profile-directory=Default")
    
    # Browser ko normal mode mein kholna (Headless nahi)
    driver = uc.Chrome(options=options)
    
    try:
        print("\n[STEP 1] Browser khul gaya hai. LinkedIn/Indeed par jao aur Login karo.")
        print("[STEP 2] 'Remember Me' par click karna mat bhulna.")
        print("[STEP 3] Jab login ho jaye aur home page dikhne lage, tab yahan wapas aao.\n")
        
        driver.get("https://www.linkedin.com/login")
        
        input("--- Login karne ke baad yahan ENTER dabayein taaki profile save ho jaye... ---")
        
        print("Saving session and closing browser...")
        time.sleep(2)
        
    finally:
        driver.quit()
        print("\n✅ Profile successfully save ho gayi hai! Ab aap main scraper chala sakte hain.")

if __name__ == "__main__":
    create_job_profile()