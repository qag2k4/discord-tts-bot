import discord
from discord.ext import commands
from gtts import gTTS
import os
import asyncio
from keep_alive import keep_alive  # Import server để giữ bot sống trên Render

# --- CẤU HÌNH BOT ---
# Lấy Token từ biến môi trường trên Render
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
    # 1. Kiểm tra người dùng có trong voice channel không
    if ctx.author.voice is None:
        await ctx.send("❌ Bạn phải vào voice channel trước.")
        return

    channel = ctx.author.voice.channel
    voice_client = ctx.voice_client

    # 2. Bot kết nối vào kênh (hoặc chuyển kênh)
    if voice_client is None:
        voice_client = await channel.connect()
    elif voice_client.channel != channel:
        await voice_client.move_to(channel)

    # 3. Tạo file âm thanh từ văn bản
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

    # 5. XÁC ĐỊNH ĐƯỜNG DẪN FFMPEG (Quan trọng cho Render)
    # Nếu file build.sh chạy đúng, ffmpeg sẽ nằm ở ./bin/ffmpeg
    if os.path.exists("./bin/ffmpeg"):
        ffmpeg_executable = "./bin/ffmpeg"
    else:
        # Dự phòng cho trường hợp chạy trên máy tính cá nhân
        ffmpeg_executable = "ffmpeg"

    # 6. Phát âm thanh
    try:
        # Hàm này sẽ chạy sau khi bot nói xong để xóa file
        def after_playing(error):
            if os.path.exists(file_path):
                os.remove(file_path)
            if error:
                print(f"Lỗi khi phát: {error}")

        # Truyền đường dẫn executable vào đây để Render nhận diện được FFmpeg
        source = discord.FFmpegPCMAudio(file_path, executable=ffmpeg_executable)
        voice_client.play(source, after=after_playing)
        
        await ctx.send(f"🔊 Đang nói: **{text}**")

    except Exception as e:
        await ctx.send("❌ Lỗi phát âm thanh. Có thể do Render chưa cài được FFmpeg.")
        print(f"Chi tiết lỗi: {e}")

# --- WEB SERVER (Giữ bot sống) ---
keep_alive()

# --- CHẠY BOT ---
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ Lỗi: Chưa có TOKEN trong Environment Variables!")
