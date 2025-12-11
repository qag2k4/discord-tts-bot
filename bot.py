import discord
from discord.ext import commands
from gtts import gTTS
import os

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot đã online: {bot.user}")

@bot.command()
async def say(ctx, *, text):
    if ctx.author.voice is None:
        await ctx.send("❌ Bạn phải vào voice channel trước.")
        return

    channel = ctx.author.voice.channel
    voice_client = ctx.voice_client

    if voice_client is None:
        voice_client = await channel.connect()
    else:
        await voice_client.move_to(channel)

    tts = gTTS(text=text, lang="vi")
    tts.save("tts.mp3")

    voice_client.play(discord.FFmpegPCMAudio("tts.mp3"))

    while voice_client.is_playing():
        await discord.utils.sleep_until(
            discord.utils.utcnow() + discord.utils.timedelta(seconds=1)
        )

    await voice_client.disconnect()
    os.remove("tts.mp3")

bot.run(TOKEN)
