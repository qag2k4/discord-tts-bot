import discord
from discord.ext import commands
import os
import threading
from flask import Flask
from gtts import gTTS
import re
import subprocess

# ================= Flask (Giữ bot online trên Render) =================
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

threading.Thread(target=run_flask, daemon=True).start()

# ================= Discord Bot =================
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

AUTO_TTS = False
AUDIO_FILE = "tts.mp3"

# ⚠️ QUAN TRỌNG: Khi dùng Docker, chỉ cần để là "ffmpeg"
# Hệ thống sẽ tự tìm thấy nó vì ta đã cài qua Dockerfile
FFMPEG_PATH = "ffmpeg"

# ================= Events =================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot online: {bot.user}")

    # Kiểm tra FFmpeg có hoạt động không
    try:
        # Gọi lệnh ffmpeg -version để xem đã cài chưa
        subprocess.check_output([FFMPEG_PATH, "-version"])
        print("✅ FFmpeg đã được cài đặt thành công!")
    except Exception as e:
        print("❌ Lỗi FFmpeg (Chưa cài hoặc sai đường dẫn):", e)

# ================= Slash commands =================
@bot.tree.command(name="auto", description="Bật chế độ tự động đọc tin nhắn")
async def auto(interaction: discord.Interaction):
    global AUTO_TTS
    AUTO_TTS = True
    await interaction.response.send_message("🔊 Đã BẬT chế độ tự động đọc.", ephemeral=True)

@bot.tree.command(name="tat", description="Tắt chế độ tự động đọc tin nhắn")
async def tat(interaction: discord.Interaction):
    global AUTO_TTS
    AUTO_TTS = False
    await interaction.response.send_message("🔇 Đã TẮT chế độ tự động đọc.", ephemeral=True)

@bot.tree.command(name="noi", description="Bot vào voice và nói văn bản bạn nhập")
async def noi(interaction: discord.Interaction, text: str):
    await interaction.response.defer() # Tránh timeout nếu xử lý lâu

    if not interaction.user.voice:
        await interaction.followup.send("❌ Bạn cần vào kênh thoại trước!", ephemeral=True)
        return

    channel = interaction.user.voice.channel
    vc = interaction.guild.voice_client

    # Nếu bot chưa vào thì cho bot vào
    if not vc:
        vc = await channel.connect()

    # Nếu bot đang ở kênh khác thì chuyển sang kênh của user
    if vc.channel.id != channel.id:
        await vc.move_to(channel)

    speak(vc, text)
    await interaction.followup.send(f"🗣️ Đang nói: {text}", ephemeral=True)

# ================= TTS Processing =================
def clean_text(text: str) -> str:
    text = re.sub(r"http\S+", "", text)        # Bỏ link
    text = re.sub(r"<:.+?:\d+>", "", text)     # Bỏ custom emoji
    text = re.sub(r"[^\w\sÀ-ỹ]", "", text)     # Bỏ ký tự đặc biệt
    return text.strip()

def speak(vc, text):
    # Nếu bot đang nói thì bỏ qua (hoặc bạn có thể dùng queue nếu muốn nâng cao)
    if vc.is_playing():
        return

    text = clean_text(text)
    if not text:
        return

    # Tạo file âm thanh từ gTTS
    try:
        tts = gTTS(text=text, lang="vi")
        tts.save(AUDIO_FILE)

        # Phát âm thanh vào Discord
        source = discord.FFmpegPCMAudio(
            AUDIO_FILE,
            executable=FFMPEG_PATH,
            before_options="-loglevel quiet", # Giấu log rác của ffmpeg
            options="-vn"
        )
        vc.play(source)
    except Exception as e:
        print(f"Lỗi khi phát âm thanh: {e}")

# ================= Auto TTS Logic =================
@bot.event
async def on_message(message):
    # Bỏ qua tin nhắn của bot hoặc nếu chưa bật Auto
    if message.author.bot or not AUTO_TTS:
        return

    # Chỉ hoạt động trong server (không DM)
    if not message.guild:
        return

    vc = message.guild.voice_client
    
    # Chỉ đọc nếu bot đang trong voice và người chat cũng ở trong voice đó
    if not vc or not message.author.voice or message.author.voice.channel != vc.channel:
        return

    speak(vc, message.content)
    
    # Dòng này cần thiết để lệnh text truyền thống (nếu có) vẫn chạy
    await bot.process_commands(message)

# ================= Run Bot =================
bot.run(os.getenv("TOKEN"))
