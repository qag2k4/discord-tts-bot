import discord
from discord.ext import commands
import os
from gtts import gTTS

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot online: {bot.user}")

@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
    else:
        await ctx.send("❌ Bạn chưa vào voice!")

@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.guild and message.guild.voice_client:
        text = message.content
        tts = gTTS(text=text, lang="vi")
        tts.save("tts.mp3")

        vc = message.guild.voice_client
        if not vc.is_playing():
            vc.play(discord.FFmpegPCMAudio("tts.mp3"))

    await bot.process_commands(message)

bot.run(os.getenv("TOKEN"))
