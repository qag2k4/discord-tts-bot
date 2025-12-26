import discord
from discord.ext import commands
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

# ====== HÀM LỌC TEXT ======
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

    # bỏ ký tự lặp / thừa
    text = re.sub(r"\s+", " ", text).strip()

    return text


# ====== PLAY TTS QUEUE ======
async def play_queue(guild):
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


# ====== EVENTS ======
@bot.event
async def on_ready():
    print(f"Bot online: {bot.user}")

@bot.command()
async def join(ctx):
    if ctx.author.voice:
        await ctx.author.voice.channel.connect()
        await ctx.send("🔊 Bot đã vào voice")
    else:
        await ctx.send("❌ Bạn chưa vào voice")

@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Bot đã rời voice")

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    vc = message.guild.voice_client
    if not vc or not vc.is_connected():
        return

    text = clean_text(message.content)
    if not text:
        return

    await tts_queue.put(text)
    await play_queue(message.guild)

    await bot.process_commands(message)


bot.run(os.getenv("TOKEN"))
