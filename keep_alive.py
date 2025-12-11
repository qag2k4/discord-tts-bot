from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot đang chạy ngon lành!"

def run():
    # Quan trọng: Phải set host là 0.0.0.0 và port 8080 (hoặc 10000)
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
