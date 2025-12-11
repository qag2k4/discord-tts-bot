import discord
from discord.ext import commands
from gtts import gTTS
import os
import asyncio
from keep_alive import keep_alive  # Import web server ảo

# Lấy token từ biến môi trường (Cài đặt trong Render)
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
    # Kiểm tra người dùng có trong voice channel không
    if ctx.author.voice is None:
        await ctx.send("❌ Bạn phải vào voice channel trước.")
        return

    channel = ctx.author.voice.channel
    voice_client = ctx.voice_client

    # Kết nối hoặc di chuyển bot đến channel
    if voice_client is None:
        voice_client = await channel.connect()
    elif voice_client.channel != channel:
        await voice_client.move_to(channel)

    # Tạo file âm thanh từ văn bản
    try:
        tts = gTTS(text=text, lang="vi")
        tts.save("tts.mp3")
    except Exception as e:
        await ctx.send(f"❌ Lỗi tạo giọng nói: {e}")
        return

    # Kiểm tra nếu đang nói thì dừng lại
    if voice_client.is_playing():
        voice_client.stop()

    # Phát âm thanh
    try:
        # options='-reconnect 1' giúp ổn định kết nối stream nếu cần
        source = discord.FFmpegPCMAudio("tts.mp3")
        voice_client.play(source)
    except Exception as e:
        await ctx.send("❌ Lỗi FFmpeg: Chưa cài đặt FFmpeg hoặc lỗi file.")
        print(f"Lỗi: {e}")
        return

    # Đợi cho đến khi nói xong
    while voice_client.is_playing():
        await asyncio.sleep(1)

    # Ngắt kết nối và xóa file
    await voice_client.disconnect()
    
    if os.path.exists("tts.mp3"):
        os.remove("tts.mp3")

# Chạy web server ảo trước khi chạy bot
keep_alive()

# Chạy bot
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ Lỗi: Chưa tìm thấy TOKEN trong biến môi trường!")
