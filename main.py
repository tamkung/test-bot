from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
import time
import requests
from datetime import datetime, timedelta

webhook_url = ""

def send_discord_notify(message):
    data = {
        'content': message
    }
    response = requests.post(webhook_url, json=data)
    if response.status_code == 204:
        print("ส่งแจ้งเตือนทางสำเร็จ")
    else:
        print("การแจ้งเตือนทางล้มเหลว:", response.text)


# Initialize the Chrome WebDriver
s = Service('/usr/local/bin/chromedriver')
driver = webdriver.Chrome(service=s)

# 1. เปิดหน้า Login ของ Twitter
driver.get('https://twitter.com/login')

# รอให้หน้าเว็บโหลด
time.sleep(5)

# 2. กรอก Username และ Password
try:
    # รอให้ฟิลด์กรอก Username ปรากฏ
    username_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "text"))
    )
    username_field.send_keys('TamTa28568')
    #username_field.send_keys('TestBot093')

    # คลิกปุ่ม Next
    username_field.send_keys(Keys.RETURN)
    time.sleep(2)

    # กรอก Password
    password_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "password"))
    )
    password_field.send_keys('')

    # คลิกปุ่ม Login
    password_field.send_keys(Keys.RETURN)

except Exception as e:
    print(f"การ Login ล้มเหลว: {e}")
    driver.quit()
    exit()

# รอให้หน้าเว็บโหลด
time.sleep(5)
url = "https://twitter.com/search?q=%23FujiiKazeBKK2024&src=recent_search_click&f=live"
driver.get(url)

# Keep track of already notified tweet links along with the timestamp when they were added
sent_tweet_links = {}

# Time to keep a tweet link in the set (e.g., 5 minutes)
TWEET_EXPIRY_TIME = timedelta(minutes=5)

def cleanup_old_tweets():
    current_time = datetime.now()
    # Remove entries older than TWEET_EXPIRY_TIME
    expired_links = [link for link, added_time in sent_tweet_links.items() if current_time - added_time > TWEET_EXPIRY_TIME]
    for link in expired_links:
        del sent_tweet_links[link]
    print(f"Cleaned up {len(expired_links)} expired tweet links.")

# ฟังก์ชันดึงโพสต์ที่ใช้แฮชแท็กและอายุโพสต์ไม่เกิน 1 นาท
def get_latest_tweets():
    try:
        # รอให้ทวีตปรากฏ (ใช้เวลา 10 วินาที)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//div[@data-testid="tweetText"]'))
        )
        
        # ดึงทวีตจากหน้าเว็บ
        tweets = driver.find_elements(By.XPATH, '//article[@data-testid="tweet"]')
        print("จำนวนทวีตที่พบ:", len(tweets))
        
        tweet_data = []
        for tweet in tweets:
            try:
                # ดึง element ที่เกี่ยวข้องกับเวลา
                tweet_time_element = tweet.find_element(By.XPATH, './/time')
                tweet_time = tweet_time_element.get_attribute('datetime')
                
                tweet_time_utc = datetime.strptime(tweet_time, "%Y-%m-%dT%H:%M:%S.000Z")
                tweet_time_gmt7 = tweet_time_utc + timedelta(hours=7)
                
                current_time_gmt7 = datetime.now()
                
                # ตรวจสอบว่าเวลาปัจจุบันไม่เกิน 120 วินาที
                time_diff = current_time_gmt7 - tweet_time_gmt7
                if time_diff.total_seconds() <= 120:
                    tweet_text = tweet.find_element(By.XPATH, './/div[@data-testid="tweetText"]').text
                    
                    if "งานจะจัดวันที่" not in tweet_text: 
                        # ดึงลิงก์จากแท็ก <a> ที่มีลิงก์โพสต์ทวีต
                        try:
                            tweet_link_element = tweet.find_element(By.XPATH, './/a[contains(@href, "/status/")]')
                            tweet_link = tweet_link_element.get_attribute('href')
                        
                            # ตรวจสอบว่าทวีตนี้ยังไม่ได้ถูกส่งแจ้งเตือน
                            if tweet_link not in sent_tweet_links:
                                tweet_data.append({
                                    'text': tweet_text,
                                    'link': tweet_link
                                })
                                # เพิ่มลิงก์ทวีตเข้าไปใน dict ของลิงก์ที่ส่งแล้ว พร้อมบันทึกเวลาที่เพิ่ม
                                sent_tweet_links[tweet_link] = current_time_gmt7
                        except Exception as e:
                            print(e)
                            continue
            except Exception as e:
                print(f"An error occurred while fetching tweet data: {e}")
                continue
        return tweet_data
    
    except Exception as e:
        print(f"ไม่พบข้อมูลทวีตหรือเกิดข้อผิดพลาด: {e}")
        return []

try:
    while True:
        latest_tweets = get_latest_tweets()
        if latest_tweets:
            for tweet in latest_tweets:
                message = f"<=====โพสต์ใหม่=====>\n{tweet['text']}\nลิงก์: {tweet['link']}"
                send_discord_notify(message)
        
        time.sleep(40)  # หน่วงเวลา 40 วินาที
        driver.refresh()  # รีเฟรชหน้าเว็บเพื่อดึงทวีตใหม่
        cleanup_old_tweets()  # Run cleanup every iteration
except KeyboardInterrupt:
    print("โปรแกรมหยุดทำงาน")
finally:
    driver.quit()

