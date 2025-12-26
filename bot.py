import discord
from discord.ext import commands
from discord import app_commands
import os
from gtts import gTTS
import uuid
import re
import asyncio

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

tts_queue = asyncio.Queue()
is_playing = False
auto_tts = False  # trạng thái auto nói


# ===== LỌC TEXT =====
def clean_text(text: str) -> str:
    text = re.sub(r"http\S+|www\S+", "", text)  # bỏ link
    text = re.sub(r"[\U00010000-\U0010ffff]", "", text)  # bỏ emoji
    return re.sub(r"\s+", " ", text).strip()


# ===== PLAY QUEUE =====
async def play_queue(guild: discord.Guild):
    global is_playing
    if is_playing:
        return

    vc = guild.voice_client
    if not vc:
        return

    is_playing = True

    while not tts_queue.empty():
        text = await tts_queue.get()
        filename = f"tts_{uuid.uuid4()}.mp3"
        gTTS(text=text, lang="vi").save(filename)

        vc.play(
            discord.FFmpegPCMAudio(filename),
            after=lambda e: os.remove(filename)
        )

        while vc.is_playing():
            await asyncio.sleep(0.3)

    is_playing = False


# ===== EVENTS =====
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Bot online: {bot.user}")


# ===== SLASH COMMAND =====
@bot.tree.command(name="nói", description="Bot tự vào voice và nói")
@app_commands.describe(noi_dung="Nội dung cần nói")
async def noi(interaction: discord.Interaction, noi_dung: str):
    await interaction.response.defer()

    if not interaction.user.voice:
        await interaction.followup.send("❌ Bạn chưa vào voice")
        return

    vc = interaction.guild.voice_client
    if not vc:
        await interaction.user.voice.channel.connect()
        vc = interaction.guild.voice_client

    text = clean_text(noi_dung)
    if not text:
        await interaction.followup.send("❌ Nội dung không hợp lệ")
        return

    await tts_queue.put(text)
    await play_queue(interaction.guild)

    await interaction.followup.send(f"🗣️ Bot nói: **{text}**")


@bot.tree.command(name="auto", description="Bật auto nói")
async def auto(interaction: discord.Interaction):
    global auto_tts
    auto_tts = True
    await interaction.response.send_message("✅ Đã BẬT auto nói")


@bot.tree.command(name="tat", description="Tắt auto nói")
async def tat(interaction: discord.Interaction):
    global auto_tts
    auto_tts = False
    await interaction.response.send_message("🛑 Đã TẮT auto nói")


@bot.tree.command(name="leave", description="Bot rời voice")
async def leave(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("👋 Bot đã rời voice")
    else:
        await interaction.response.send_message("❌ Bot chưa ở voice")


# ===== AUTO TTS KHI CHAT =====
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.guild:
        return

    if not auto_tts:
        return

    vc = message.guild.voice_client
    if not vc or not vc.is_connected():
        return

    text = clean_text(message.content)
    if not text:
        return

    await tts_queue.put(text)
    await play_queue(message.guild)


bot.run(os.getenv("TOKEN"))
