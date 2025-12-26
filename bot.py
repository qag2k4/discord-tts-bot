import discord
from discord.ext import commands
import os
import threading
from flask import Flask
from gtts import gTTS
import re

# ================= FLASK (Render cần port) =================
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_flask, daemon=True).start()

# ================= DISCORD BOT =================
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

AUTO_TTS = False

@bot.event
async def on_ready():
    await bot.tree.sync()   # 🔥 CỰC KỲ QUAN TRỌNG
    print(f"✅ Bot online: {bot.user}")
    print("✅ Slash commands synced")

# ================= SLASH COMMANDS =================
@bot.tree.command(name="auto", description="Bật auto TTS")
async def auto(interaction: discord.Interaction):
    global AUTO_TTS
    AUTO_TTS = True
    await interaction.response.send_message("🔊 Đã bật auto nói")

@bot.tree.command(name="tat", description="Tắt auto TTS")
async def tat(interaction: discord.Interaction):
    global AUTO_TTS
    AUTO_TTS = False
    await interaction.response.send_message("🔇 Đã tắt auto nói")

@bot.tree.command(name="noi", description="Bot vào voice và nói")
async def noi(interaction: discord.Interaction, text: str):
    if not interaction.user.voice:
        await interaction.response.send_message(
            "❌ Bạn phải vào voice trước", ephemeral=True
        )
        return

    await interaction.response.send_message("🗣️ Đang nói...")

    channel = interaction.user.voice.channel
    if not interaction.guild.voice_client:
        await channel.connect()

    speak(interaction.guild.voice_client, text)

# ================= TTS =================
def clean_text(text: str) -> str:
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"<:.+?:\d+>", "", text)
    text = re.sub(r"[^\w\sÀ-ỹ]", "", text)
    return text.strip()

def speak(vc, text):
    text = clean_text(text)
    if not text:
        return

    tts = gTTS(text=text, lang="vi")
    tts.save("tts.mp3")

    if not vc.is_playing():
        vc.play(discord.FFmpegPCMAudio("tts.mp3"))

# ================= AUTO MODE =================
@bot.event
async def on_message(message):
    if message.author.bot or not AUTO_TTS:
        return

    if message.author.voice and message.guild.voice_client:
        speak(message.guild.voice_client, message.content)

    await bot.process_commands(message)

bot.run(os.getenv("TOKEN"))
