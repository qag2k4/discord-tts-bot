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


# ===== LỌC TEXT =====
def clean_text(text: str) -> str:
    # bỏ link
    text = re.sub(r"http\S+|www\S+", "", text)

    # bỏ emoji
    text = re.sub(
        r"[\U00010000-\U0010ffff]",
        "",
        text,
        flags=re.UNICODE
    )

    # bỏ khoảng trắng thừa
    return re.sub(r"\s+", " ", text).strip()


# ===== PLAY QUEUE =====
async def play_queue(guild: discord.Guild):
    global is_playing
    if is_playing:
        return

    is_playing = True
    vc = guild.voice_client

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


# ===== SLASH COMMANDS =====
@bot.tree.command(name="nói", description="Bot sẽ nói nội dung bạn nhập")
@app_commands.describe(noi_dung="Nội dung cần nói")
async def noi(interaction: discord.Interaction, noi_dung: str):
    await interaction.response.defer()

    vc = interaction.guild.voice_client
    if not vc or not vc.is_connected():
        await interaction.followup.send("❌ Bot chưa ở trong voice")
        return

    text = clean_text(noi_dung)
    if not text:
        await interaction.followup.send("❌ Nội dung không hợp lệ")
        return

    await tts_queue.put(text)
    await play_queue(interaction.guild)

    await interaction.followup.send(f"🗣️ Đang nói: **{text}**")


@bot.tree.command(name="join", description="Bot vào voice của bạn")
async def join(interaction: discord.Interaction):
    if interaction.user.voice:
        await interaction.user.voice.channel.connect()
        await interaction.response.send_message("🔊 Bot đã vào voice")
    else:
        await interaction.response.send_message("❌ Bạn chưa vào voice")


@bot.tree.command(name="leave", description="Bot rời voice")
async def leave(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("👋 Bot đã rời voice")
    else:
        await interaction.response.send_message("❌ Bot chưa ở voice")


bot.run(os.getenv("TOKEN"))
