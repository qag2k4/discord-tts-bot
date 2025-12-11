import discord
import google.generativeai as genai
import os
import io
import PIL.Image
import asyncio
from threading import Thread
from flask import Flask

# ==========================================
# PHẦN GIỮ BOT ONLINE (KEEP ALIVE)
# ==========================================
app = Flask('')

@app.route('/')
def home():
    return "Bot đang sống nhăn răng!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ==========================================
# CẤU HÌNH BOT
# ==========================================
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Cấu hình AI
genai.configure(api_key=GEMINI_API_KEY)
model_pro = genai.GenerativeModel(model_name='gemini-1.5-pro')
model_flash = genai.GenerativeModel(model_name='gemini-1.5-flash')

user_chats = {} 
active_channels = set() # Lưu các kênh được phép chat

# Dùng Client thường, KHÔNG dùng commands.Bot để tránh lỗi CommandNotFound
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'{client.user} đã xuất sơn!')
    # Đổi trạng thái để bạn biết code mới đã chạy
    await client.change_presence(activity=discord.Game(name="Gõ !goi để gọi ta"))

@client.event
async def on_message(message):
    if message.author == client.user: return

    # Lấy ID kênh
    channel_id = message.channel.id
    is_dm = isinstance(message.channel, discord.DMChannel)

    # --- CỤM LỆNH ĐIỀU KHIỂN ---
    msg_content = message.content.strip().lower()

    if msg_content == "!goi":
        active_channels.add(channel_id)
        await message.channel.send("🔔 **Tiểu Thư Đồng đã tới!** Đại hiệp cứ hỏi, tại hạ sẽ túc trực ở đây.")
        return

    if msg_content == "!thoi":
        if channel_id in active_channels:
            active_channels.remove(channel_id)
            await message.channel.send("💤 **Cáo lui!** Khi nào cần đại hiệp cứ gõ `!goi`.")
        else:
            await message.channel.send("Tại hạ có đang ở đây đâu mà đuổi?")
        return

    # --- QUY TẮC IM LẶNG ---
    # Nếu không phải DM và chưa được gọi (!goi) thì bỏ qua
    if (channel_id not in active_channels) and (not is_dm):
        return

    # --- XỬ LÝ AI ---
    try:
        async with message.channel.typing():
            user_id = message.author.id
            content_to_send = []
            if message.content: content_to_send.append(message.content)
            
            # Xử lý ảnh
            if message.attachments:
                for attachment in message.attachments:
                    if any(attachment.content_type.startswith(t) for t in ["image/"]):
                        # Tải ảnh về RAM
                        image_data = await attachment.read()
                        image = PIL.Image.open(io.BytesIO(image_data))
                        content_to_send.append(image)

            if not content_to_send: return

            if user_id not in user_chats:
                user_chats[user_id] = model_pro.start_chat(history=[])

            chat_session = user_chats[user_id]
            sent_message = await message.channel.send("Đang suy ngẫm...")

            # Hàm stream để gửi tin dài
            async def stream_response(session, content):
                response_stream = session.send_message(content, stream=True)
                collected_text = ""
                last_edit_length = 0
                for chunk in response_stream:
                    if chunk.text:
                        collected_text += chunk.text
                        # Cập nhật mỗi 100 ký tự để tránh spam API Discord
                        if len(collected_text) - last_edit_length > 100:
                            if len(collected_text) < 2000:
                                await sent_message.edit(content=collected_text)
                                last_edit_length = len(collected_text)
                            else:
                                await sent_message.edit(content=collected_text[:2000])
                
                if 0 < len(collected_text) < 2000: 
                    await sent_message.edit(content=collected_text)
                elif len(collected_text) >= 2000:
                    await sent_message.edit(content=collected_text[:2000] + "\n...(còn tiếp)")

            try:
                await stream_response(chat_session, content_to_send)
            except Exception as e:
                # Nếu Pro lỗi thì chuyển sang Flash
                print(f"Lỗi Pro: {e}, chuyển sang Flash")
                old_history = chat_session.history
                new_session = model_flash.start_chat(history=old_history)
                user_chats[user_id] = new_session
                await stream_response(new_session, content_to_send)

    except Exception as e:
        print(f"Lỗi hệ thống: {e}")
        await message.channel.send("Tại hạ bị tẩu hỏa nhập ma rồi.")

if __name__ == "__main__":
    keep_alive() # Chạy server giả
    client.run(DISCORD_TOKEN)
