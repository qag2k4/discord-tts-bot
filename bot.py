import discord
from discord.ext import commands
from gtts import gTTS
import os
import asyncio
from keep_alive import keep_alive  # <--- THÊM DÒNG NÀY

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
    if ctx.author.voice is None:
        await ctx.send("❌ Bạn phải vào voice channel trước.")
        return

    channel = ctx.author.voice.channel
    voice_client = ctx.voice_client

    if voice_client is None:
        voice_client = await channel.connect()
    elif voice_client.channel != channel:
        await voice_client.move_to(channel)

    try:
        tts = gTTS(text=text, lang="vi")
        tts.save("tts.mp3")
    except Exception as e:
        await ctx.send(f"❌ Lỗi tạo giọng nói: {e}")
        return

    if voice_client.is_playing():
        voice_client.stop()

    try:
        # executable='./ffmpeg' chỉ cần nếu bạn dùng build script cài ffmpeg riêng
        # Nếu chưa cài ffmpeg, dòng này sẽ lỗi nhưng bot vẫn chạy được.
        voice_client.play(discord.FFmpegPCMAudio("tts.mp3"))
    except Exception as e:
        await ctx.send("❌ Lỗi phát âm thanh (có thể do thiếu FFmpeg).")
        print(f"Lỗi: {e}")

    while voice_client.is_playing():
        await asyncio.sleep(1)

    # Không disconnect ngay để tránh lỗi kết nối lại liên tục
    # await voice_client.disconnect() 
    if os.path.exists("tts.mp3"):
        os.remove("tts.mp3")

# --- PHẦN QUAN TRỌNG NHẤT ĐỂ SỬA LỖI TIMEOUT ---
keep_alive()  # <--- Chạy web server giả
# -----------------------------------------------

if TOKEN:
    bot.run(TOKEN)
else:
    print("Chưa có TOKEN!")
