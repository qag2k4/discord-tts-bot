import discord
from discord.ext import commands
import os
import threading
from flask import Flask
from gtts import gTTS
import re
import subprocess

# ================= Flask (mở port cho Render) =================
app = Flask(__name__)

@app.route("/")
def home():
    return "OK"

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
FFMPEG_PATH = "/usr/bin/ffmpeg"  # ⚠️ RẤT QUAN TRỌNG TRÊN RENDER

# ================= Events =================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot online: {bot.user}")

    # test ffmpeg
    try:
        subprocess.check_output([FFMPEG_PATH, "-version"])
        print("✅ FFmpeg OK")
    except Exception as e:
        print("❌ FFmpeg FAIL:", e)

# ================= Slash commands =================
@bot.tree.command(name="auto", description="Bật auto nói")
async def auto(interaction: discord.Interaction):
    global AUTO_TTS
    AUTO_TTS = True
    await interaction.response.send_message("🔊 Đã bật auto nói", ephemeral=True)

@bot.tree.command(name="tat", description="Tắt auto nói")
async def tat(interaction: discord.Interaction):
    global AUTO_TTS
    AUTO_TTS = False
    await interaction.response.send_message("🔇 Đã tắt auto nói", ephemeral=True)

@bot.tree.command(name="noi", description="Bot vào voice và nói")
async def noi(interaction: discord.Interaction, text: str):
    await interaction.response.defer()

    if not interaction.user.voice:
        await interaction.followup.send("❌ Bạn chưa vào voice", ephemeral=True)
        return

    channel = interaction.user.voice.channel
    vc = interaction.guild.voice_client

    if not vc:
        vc = await channel.connect()

    speak(vc, text)
    await interaction.followup.send("🗣️ Đang nói...", ephemeral=True)

# ================= TTS =================
def clean_text(text: str) -> str:
    text = re.sub(r"http\S+", "", text)        # bỏ link
    text = re.sub(r"<:.+?:\d+>", "", text)     # bỏ emoji custom
    text = re.sub(r"[^\w\sÀ-ỹ]", "", text)     # bỏ ký tự lạ
    return text.strip()

def speak(vc, text):
    if vc.is_playing():
        return

    text = clean_text(text)
    if not text:
        return

    gTTS(text=text, lang="vi").save(AUDIO_FILE)

    source = discord.FFmpegPCMAudio(
        AUDIO_FILE,
        executable=FFMPEG_PATH,
        before_options="-loglevel quiet",
        options="-vn"
    )

    vc.play(source)

# ================= Auto TTS =================
@bot.event
async def on_message(message):
    if message.author.bot or not AUTO_TTS:
        return

    if not message.guild:
        return

    vc = message.guild.voice_client
    if not vc or not message.author.voice:
        return

    speak(vc, message.content)
    await bot.process_commands(message)

# ================= Run =================
bot.run(os.getenv("TOKEN"))
