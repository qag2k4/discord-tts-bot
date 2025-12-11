import discord
from discord.ext import commands
from gtts import gTTS
import os
import asyncio

# Kiểm tra xem file keep_alive có tồn tại không để tránh lỗi import
try:
    from keep_alive import keep_alive
    HAS_KEEP_ALIVE = True
except ImportError:
    HAS_KEEP_ALIVE = False
    print("⚠️ Không tìm thấy module keep_alive. Bot sẽ chạy cục bộ.")

# Lấy token từ biến môi trường
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot đã online: {bot.user}")

@bot.command()
async def say(ctx, *, text):
    # 1. Kiểm tra người dùng có trong voice không
    if ctx.author.voice is None:
        await ctx.send("❌ Bạn phải vào voice channel trước.")
        return

    channel = ctx.author.voice.channel
    voice_client = ctx.voice_client

    # 2. Kết nối hoặc chuyển kênh
    if voice_client is None:
        voice_client = await channel.connect()
    elif voice_client.channel != channel:
        await voice_client.move_to(channel)

    # 3. Tạo file âm thanh
    file_path = "tts.mp3"
    try:
        tts = gTTS(text=text, lang="vi")
        tts.save(file_path)
    except Exception as e:
        await ctx.send(f"❌ Lỗi tạo giọng nói: {e}")
        return

    # 4. Dừng âm thanh cũ nếu đang phát
    if voice_client.is_playing():
        voice_client.stop()

    # 5. Phát âm thanh
    try:
        # Hàm callback để xóa file sau khi phát xong
        def after_playing(error):
            if os.path.exists(file_path):
                os.remove(file_path)
            if error:
                print(f"Lỗi khi phát: {error}")

        # Kiểm tra FFmpeg (Quan trọng)
        source = discord.FFmpegPCMAudio(file_path)
        voice_client.play(source, after=after_playing)

    except Exception as e:
        await ctx.send("❌ Lỗi phát âm thanh. Hãy chắc chắn server đã cài FFmpeg.")
        print(f"Chi tiết lỗi FFmpeg: {e}")

# --- WEB SERVER (Cho Replit/Uptimerobot) ---
if HAS_KEEP_ALIVE:
    keep_alive()
# -------------------------------------------

if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ Lỗi: Chưa có TOKEN trong Environment Variables!")
