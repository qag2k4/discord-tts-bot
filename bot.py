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

# ⚠️ QUAN TRỌNG: Với Docker trên Render, chỉ cần để là "ffmpeg"
FFMPEG_PATH = "ffmpeg"

# ================= Events =================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot online: {bot.user}")

    # Kiểm tra FFmpeg
    try:
        subprocess.check_output([FFMPEG_PATH, "-version"])
        print("✅ FFmpeg đã sẵn sàng!")
    except Exception as e:
        print("❌ Lỗi FFmpeg:", e)

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

# 🆕 Lệnh MỚI QUAN TRỌNG: Dùng khi bot bị kẹt hoặc không chịu vào phòng
@bot.tree.command(name="out", description="Đá bot ra khỏi phòng và reset kết nối (Dùng khi lỗi)")
async def out(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect(force=True)
        await interaction.response.send_message("👋 Đã reset bot. Hãy thử gọi lại `/noi`", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Bot hiện không ở trong phòng nào cả.", ephemeral=True)

@bot.tree.command(name="noi", description="Bot vào voice và nói văn bản bạn nhập")
async def noi(interaction: discord.Interaction, text: str):
    await interaction.response.defer() # Tránh timeout

    if not interaction.user.voice:
        await interaction.followup.send("❌ Bạn cần vào kênh thoại trước!", ephemeral=True)
        return

    channel = interaction.user.voice.channel
    vc = interaction.guild.voice_client

    try:
        # Nếu bot chưa vào thì connect
        if not vc:
            vc = await channel.connect()
        
        # Nếu bot đang ở kênh khác thì move qua
        elif vc.channel.id != channel.id:
            await vc.move_to(channel)

    except Exception as e:
        # Nếu lỗi kết nối (thường do bot bị kẹt), thử reset
        await interaction.followup.send("⚠️ Bot bị kẹt kết nối. Đang thử reset...", ephemeral=True)
        if vc:
            await vc.disconnect(force=True)
        vc = await channel.connect()

    speak(vc, text)
    await interaction.followup.send(f"🗣️ Đang nói: {text}", ephemeral=True)

# ================= TTS Processing =================
def clean_text(text: str) -> str:
    text = re.sub(r"http\S+", "", text)        # Bỏ link
    text = re.sub(r"<:.+?:\d+>", "", text)     # Bỏ custom emoji
    text = re.sub(r"[^\w\sÀ-ỹ]", "", text)     # Bỏ ký tự đặc biệt
    return text.strip()

def speak(vc, text):
    # Nếu bot đang nói thì bỏ qua
    if vc.is_playing():
        return

    text = clean_text(text)
    if not text:
        return

    try:
        # Tạo file âm thanh
        tts = gTTS(text=text, lang="vi")
        tts.save(AUDIO_FILE)

        # Phát âm thanh
        source = discord.FFmpegPCMAudio(
            AUDIO_FILE,
            executable=FFMPEG_PATH,
            before_options="-loglevel quiet",
            options="-vn"
        )
        vc.play(source)
    except Exception as e:
        print(f"Lỗi TTS: {e}")

# ================= Auto TTS Logic =================
@bot.event
async def on_message(message):
    if message.author.bot or not AUTO_TTS:
        return

    if not message.guild:
        return

    vc = message.guild.voice_client
    
    # Chỉ đọc nếu bot và người chat cùng phòng voice
    if not vc or not message.author.voice or message.author.voice.channel != vc.channel:
        return

    speak(vc, message.content)
    
    await bot.process_commands(message)

# ================= Run Bot =================
bot.run(os.getenv("TOKEN"))
