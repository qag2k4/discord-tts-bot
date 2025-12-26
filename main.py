import discord
from discord.ext import commands
from gtts import gTTS
import os

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot da dang nhap: {bot.user}")

@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
        await ctx.send("🤖 Bot da vao kenh voice!")
    else:
        await ctx.send("❌ Ban phai vao voice truoc!")

@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Bot da roi voice!")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.guild and message.guild.voice_client:
        vc = message.guild.voice_client

        tts = gTTS(text=message.content, lang="vi")
        tts.save("tts.mp3")

        if not vc.is_playing():
            vc.play(discord.FFmpegPCMAudio("tts.mp3"))

    await bot.process_commands(message)

bot.run(os.getenv("TOKEN"))
