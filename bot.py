import urllib.request
import json
import os
from io import BytesIO
from rembg import remove
from PIL import Image

# ⚠️ توکن بات تلگرامت رو اینجا بذار
TOKEN = "8771734193:AAEokQwTdZDBCdM2_9pNsHD4H10zaZymQi8"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

def call_api(method, params=None, files=None):
    """تابع کمکی برای ارتباط با API تلگرام"""
    url = f"{BASE_URL}/{method}"
    
    if files:
        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        body = b""
        for key, value in params.items():
            body += f"--{boundary}\r\n".encode()
            body += f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode()
            body += f"{value}\r\n".encode()
        
        for field_name, file_tuple in files.items():
            filename, file_data = file_tuple
            body += f"--{boundary}\r\n".encode()
            body += f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'.encode()
            body += b"Content-Type: application/octet-stream\r\n\r\n"
            body += file_data + b"\r\n"
        
        body += f"--{boundary}--\r\n".encode()
        req = urllib.request.Request(url, data=body)
        req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    
    elif params:
        data = json.dumps(params).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    else:
        req = urllib.request.Request(url)
    
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read())

def get_updates(offset=None):
    params = {"timeout": 30}
    if offset:
        params["offset"] = offset
    return call_api("getUpdates", params)

def send_message(chat_id, text):
    return call_api("sendMessage", {"chat_id": chat_id, "text": text})

def get_file(file_id):
    return call_api("getFile", {"file_id": file_id})

def download_file(file_path):
    url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
    response = urllib.request.urlopen(url)
    return response.read()

def send_sticker(chat_id, sticker_bytes):
    files = {"sticker": ("sticker.webp", sticker_bytes)}
    return call_api("sendSticker", {"chat_id": chat_id}, files)

def remove_background(image_bytes):
    """حذف بک‌گراند عکس با rembg"""
    return remove(image_bytes)

def convert_to_sticker(image_bytes):
    """تبدیل عکس به استیکر WebP مخصوص تلگرام"""
    # حذف بک‌گراند
    no_bg = remove_background(image_bytes)
    
    # تبدیل به PNG شفاف
    img = Image.open(BytesIO(no_bg)).convert("RGBA")
    
    # ریسایز به سایز استیکر تلگرام (512x512)
    img.thumbnail((512, 512), Image.LANCZOS)
    
    # تبدیل به WebP
    output = BytesIO()
    img.save(output, format="WEBP", quality=100)
    output.seek(0)
    return output.read()

# --- شروع برنامه ---
print("⏳ در حال اتصال...")
try:
    me = call_api("getMe")
    print(f"✅ @{me['result']['username']} آماده‌ست!")
except Exception as e:
    print(f"❌ خطا: {e}")
    exit()

offset = None
print("🖼️ منتظر عکس...")
while True:
    try:
        updates = get_updates(offset)
        if updates.get("result"):
            for update in updates["result"]:
                offset = update["update_id"] + 1
                message = update.get("message")
                if not message:
                    continue
                
                chat_id = message["chat"]["id"]
                
                if "photo" in message:
                    send_message(chat_id, "🎨 در حال ساخت استیکر... صبر کن!")
                    
                    photo = message["photo"][-1]
                    file_id = photo["file_id"]
                    file_info = get_file(file_id)
                    file_path = file_info["result"]["file_path"]
                    
                    image_bytes = download_file(file_path)
                    
                    try:
                        sticker_bytes = convert_to_sticker(image_bytes)
                        send_sticker(chat_id, sticker_bytes)
                        send_message(chat_id, "✅ استیکرت آماده‌ست!")
                    except Exception as e:
                        send_message(chat_id, f"❌ خطا در ساخت استیکر: {e}")
                
                elif "text" in message:
                    text = message["text"]
                    if text == "/start":
                        send_message(chat_id, "سلام! 👋\nبه بات استیکر ساز خوش اومدی!\nیه عکس بفرست تا برات استیکر شفاف کنم! 🖼️✨")
                    else:
                        send_message(chat_id, "لطفاً یه عکس بفرست!")
                        
    except Exception as e:
        print(f"⚠️ خطا: {e}")
        import time
        time.sleep(5)