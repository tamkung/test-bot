from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import time
import requests
from datetime import datetime, timedelta

line_notify_token = ''
line_notify_api = 'https://notify-api.line.me/api/notify'

def send_line_notify(message):
    headers = {
        'Authorization': f'Bearer {line_notify_token}'
    }
    data = {
        'message': message
    }
    response = requests.post(line_notify_api, headers=headers, data=data)
    if response.status_code == 200:
        print("ส่งแจ้งเตือนสำเร็จ")
    else:
        print("การแจ้งเตือนล้มเหลว:", response.text)

# Initialize the Chrome WebDriver
s = Service('C:\webdriver\chromedriver.exe')
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
url = "https://twitter.com/search?q=%23aespa_SYNK_PARALLELLINE_inBKK%20%E0%B8%9A%E0%B8%B1%E0%B8%95%E0%B8%A3&src=recent_search_click&f=live"
driver.get(url)

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
                
                # ตรวจสอบว่าเวลาปัจจุบันไม่เกิน 80 วินาที
                time_diff = current_time_gmt7 - tweet_time_gmt7
                if time_diff.total_seconds() <= 80:
                    tweet_text = tweet.find_element(By.XPATH, './/div[@data-testid="tweetText"]').text
                    
                    # ดึงลิงก์จากแท็ก <a> ที่มีลิงก์โพสต์ทวีต
                    tweet_link_element = tweet.find_element(By.XPATH, './/a[contains(@href, "/status/")]')
                    tweet_link = tweet_link_element.get_attribute('href')
                    
                    tweet_data.append({
                        'text': tweet_text,
                        'link': tweet_link
                    })
                    
            except Exception as e:
                print(f"ไม่พบ element หรือเกิดข้อผิดพลาด: {e}")
        
        return tweet_texts
    
    except Exception as e:
        print(f"ไม่พบข้อมูลทวีตหรือเกิดข้อผิดพลาด: {e}")
        return []

try:
    while True:
        latest_tweets = get_latest_tweets()
        if latest_tweets:
            for tweet in latest_tweets:
                # ส่งข้อความพร้อมลิงค์ทวีต
                send_line_notify(f"โพสต์ใหม่ #aespa_SYNK_PARALLELLINE_inBKK: {tweet['text']}\nลิงก์: {tweet['link']}")
        time.sleep(60)
        driver.refresh()
except KeyboardInterrupt:
    print("โปรแกรมหยุดทำงาน")
finally:
    driver.quit()

