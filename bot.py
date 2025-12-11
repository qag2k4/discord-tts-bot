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
        return await ctx.send("❌ Bạn phải vào voice trước.")

    channel = ctx.author.voice.channel
    vc = await channel.connect()

    tts = gTTS(text=text, lang="vi")
    tts.save("tts.mp3")

    vc.play(discord.FFmpegPCMAudio("tts.mp3"))

    while vc.is_playing():
        await discord.utils.sleep_until(discord.utils.utcnow() + discord.utils.timedelta(seconds=1))

    await vc.disconnect()
    os.remove("tts.mp3")


bot.run(TOKEN)
