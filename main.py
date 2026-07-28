import sys
sys.stdout.reconfigure(line_buffering=True)   # Python 3.7+
import sys
import io
# Force UTF-8 for stdout/stderr (fix Unicode errors with pythonw.exe)
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
import os
import random
import shutil
import requests
import base64
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from PIL import Image
import io

print("=" * 60)
print("Telegram AI Poster - Gemini 2.5 Flash (Low Rate)")
print("=" * 60)

# -----------------------
# SETTINGS
# -----------------------
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


image_folder = os.path.join(
    BASE_DIR,
    "media",
    "images"
)


used_folder = os.path.join(
    BASE_DIR,
    "media",
    "used_images"
)

# استفاده از مدل Flash-Lite (محدودیت نرخ بالاتر)
MODEL = "models/gemini-2.5-flash-lite"  # تغییر به Lite برای نرخ بالاتر
CUSTOM_FOOTER = """

<blockquote>
📍 با ما یک قدم جلوتر باشید 🔥
👉 <a href="https://t.me/technology_channel_00">@technology_channel_00</a>
</blockquote>
"""
# -----------------------
# EMAIL SETTINGS
# -----------------------
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
RECIPIENT_EMAIL = "unesjami2020@gmail.com"         # 🔴 Where to send reports

def send_email(subject, body):
    """Send email report using Gmail SMTP"""
    try:
        msg = MIMEMultipart()
        msg["From"] = f"Telegram Channels Assistant <{EMAIL_ADDRESS}>"
        msg["To"] = RECIPIENT_EMAIL
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, RECIPIENT_EMAIL, msg.as_string())
        server.quit()
        print(f"📧 Email sent: {subject}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False

# -----------------------
# GEMINI CAPTION GENERATION
# -----------------------
def get_caption_from_gemini_with_retry(image_path, max_retries=2):
    """Send image to Gemini with intelligent retry - NO FALLBACK CAPTION"""
    
    for attempt in range(max_retries):
        try:
            img = Image.open(image_path).convert('RGB')
            img.thumbnail((800, 800))
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='JPEG', quality=80)
            img_base64 = base64.b64encode(img_bytes.getvalue()).decode('utf-8')
            img.close()
            
            prompt = """This image shows an electronics or robotics component. 
Write a short, friendly, and exciting Persian caption for a Telegram post.

Rules:
- Max 5-10 lines
- start with a catchy hook base of topic! in one line.
- Use relevant emojis (at least 1-2 emojis related to the content)
- Friendly and professional tone (In the form of an attractive Telegram post)
- Use educational topics related to the content of the image
- Tell what is in the image in a practical way
- Don't post the whole picture, just get an idea from the picture and say scientific topics about it
- Explain what it is used for
- it should have informational feeling, not ads
- Add 5 relevant hashtags at the end
- Write in Persian language
- Do NOT include any footer or link in the caption (I will add it separately)
"""
            
            url = f"https://generativelanguage.googleapis.com/v1beta/{MODEL}:generateContent?key={API_KEY}"
            payload = {
                "contents": [{
                    "parts": [
                        {"text": prompt},
                        {"inline_data": {"mime_type": "image/jpeg", "data": img_base64}}
                    ]
                }]
            }
            
            response = requests.post(url, json=payload, timeout=60)
            
            if response.status_code == 200:
                caption = response.json()['candidates'][0]['content']['parts'][0]['text']
                caption = caption.split("📍")[0].strip()
                if caption and len(caption) > 20:
                    return caption
                else:
                    print(f"  Attempt {attempt+1}: Empty caption, retrying...")
                    
            elif response.status_code == 429:
                wait_time = (attempt + 1) * 20
                print(f"  Rate limit (429) - waiting {wait_time} seconds...")
                time.sleep(wait_time)
                
            else:
                print(f"  Attempt {attempt+1}: API Error {response.status_code}")
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 15
                    time.sleep(wait_time)
                    
        except Exception as e:
            print(f"  Attempt {attempt+1}: Exception - {e}")
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 15
                time.sleep(wait_time)
    
    print(f"  ❌ Failed to get caption from Gemini after {max_retries} attempts")
    return None

# -----------------------
# TELEGRAM SEND PHOTO
# -----------------------
def send_photo_via_telegram(image_path, caption, max_retries=2):
    """Send photo using direct Telegram Bot API"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    
    for attempt in range(max_retries):
        try:
            with open(image_path, "rb") as photo:
                files = {"photo": photo}
                data = {
    "chat_id": CHANNEL_ID,
    "caption": caption[:1024],
    "parse_mode": "HTML"
}
                response = requests.post(url, data=data, files=files, timeout=120)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    return True
                else:
                    print(f"  Telegram API error: {result.get('description')}")
            else:
                print(f"  HTTP error: {response.status_code}")
        except requests.exceptions.Timeout:
            print(f"  Attempt {attempt+1} timeout")
        except Exception as e:
            print(f"  Attempt {attempt+1} failed: {e}")
        
        if attempt < max_retries - 1:
            wait_time = (attempt + 1) * 10
            print(f"  Waiting {wait_time} seconds before retry...")
            time.sleep(wait_time)
    
    return False

# -----------------------
# MAIN POST FUNCTION WITH EMAIL REPORT
# -----------------------
def post_images(num_images=2):
    images = [img for img in os.listdir(image_folder) 
              if img.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
    
    # نمایش همه فایل‌های پیدا شده برای دیباگ
    print(f"🔍 Found image files in '{image_folder}': {len(images)} files")
    print("   Files:", images)
    
    if len(images) < num_images:
        error_msg = f"❌ Only {len(images)} images found. Need at least {num_images}!"
        print(error_msg)
        send_email("❌ Telegram Bot Failed - Not Enough Images", error_msg)
        return
    
    selected = random.sample(images, num_images)
    successful_posts = 0
    failed_posts = 0
    start_time = datetime.now()
    
    for i, img in enumerate(selected, 1):
        path = os.path.join(image_folder, img)
        print(f"\n📸 [{i}/{num_images}] Analyzing: {img}")
        
        caption = get_caption_from_gemini_with_retry(path)
        
        if caption is None:
            print(f"  ⚠️ Skipping this image - no caption received from Gemini")
            failed_posts += 1
            continue
        
        # بولد کردن خط اول کپشن (رفع تورفتگی)
        lines = caption.split("\n")
        if len(lines) > 0:
            lines[0] = f"<b>{lines[0]}</b>"
        caption = "\n".join(lines)
        
        full_caption = caption + CUSTOM_FOOTER
        print(f"  ✅ Caption received from Gemini")
        
        success = send_photo_via_telegram(path, full_caption)
        
        if success:
            time.sleep(2)
            try:
                shutil.move(path, os.path.join(used_folder, img))
                print(f"  ✅ Posted and moved to used_images")
                successful_posts += 1
            except PermissionError:
                time.sleep(2)
                shutil.move(path, os.path.join(used_folder, img))
                print(f"  ✅ Moved on second attempt")
                successful_posts += 1
        else:
            print(f"  ❌ Failed to send to Telegram - skipping")
            failed_posts += 1
        
        if i < num_images:
            wait_between = 25  # فاصله بین هر پست
            print(f"  Waiting {wait_between} seconds before next image...")
            time.sleep(wait_between)
    
    # Summary
    print(f"\n🎉 Done! Successfully posted {successful_posts} out of {num_images} images.")
    print(f"🔗 Channel: {CHANNEL_ID}")
    
    # Send email report
    duration = (datetime.now() - start_time).total_seconds()
    subject = "✅ Telegram Technology Channel Posts Successfuly"
    body = f"""Telegram bot finished posting.

Channel: {CHANNEL_ID}
Target posts: {num_images}
Successfully posted: {successful_posts}
Failed: {failed_posts}
Time taken: {duration:.1f} seconds
Time: {datetime.now()}

Images processed: {', '.join(selected[:3])}{'...' if len(selected)>3 else ''}
"""
    send_email(subject, body)

# -----------------------
# RUN SCRIPT WITH ERROR HANDLING
# -----------------------
if __name__ == "__main__":
    try:
        post_images(num_images=3)   # 🟢 روزی ۲ پست
    except Exception as e:
        error_body = f"Telegram bot crashed with error:\n\n{str(e)}\n\nTime: {datetime.now()}"
        send_email("❌ Telegram Bot CRASHED", error_body)
        raise