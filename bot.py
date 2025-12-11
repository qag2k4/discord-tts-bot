import discord
from discord.ext import commands
from gtts import gTTS
import os

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.command()
async def say(ctx, *, text: str):
    if ctx.author.voice is None:
        return await ctx.send("❗ Bạn phải vào voice channel trước!")

    channel = ctx.author.voice.channel
    voice = ctx.voice_client

    if voice is None:
        voice = await channel.connect()
    else:
        await voice.move_to(channel)

    tts = gTTS(text=text, lang="vi")
    tts.save("tts.mp3")

    voice.play(discord.FFmpegPCMAudio("tts.mp3"))
    await ctx.send(f"🔊 Đang đọc: **{text}**")

@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Bot đã thoát voice channel!")
    else:
        await ctx.send("Bot không ở voice channel.")

# Dùng token lấy từ Render Environment
bot.run(os.getenv("TOKEN"))
