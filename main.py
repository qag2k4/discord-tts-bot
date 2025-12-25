import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import os
import glob
from gtts import gTTS

# ===================== TÌM FFmpeg =====================
def find_ffmpeg():
    # thử PATH trước
    from shutil import which
    path = which("ffmpeg")
    if path:
        return path

    # tìm trong nix store (Railway + Nixpacks)
    candidates = glob.glob("/nix/store/*ffmpeg*/bin/ffmpeg")
    if candidates:
        return candidates[0]

    return None


FFMPEG_PATH = find_ffmpeg()
print("🔍 ffmpeg path:", FFMPEG_PATH)

# ===================== DISCORD SETUP =====================
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot đã online: {bot.user}")


# ===================== SLASH COMMAND =====================
@bot.tree.command(name="noi", description="Bot đọc nội dung bằng giọng nói")
@app_commands.describe(noidung="Nội dung cần đọc")
async def noi(interaction: discord.Interaction, noidung: str):

    if not interaction.user.voice:
        await interaction.response.send_message(
            "❌ Bạn phải vào voice trước", ephemeral=True
        )
        return

    if not FFMPEG_PATH:
        await interaction.response.send_message(
            "❌ Không tìm thấy ffmpeg trong hệ thống", ephemeral=True
        )
        return

    channel = interaction.user.voice.channel
    vc = await channel.connect()

    try:
        await interaction.response.defer()

        tts = gTTS(text=noidung, lang="vi")
        tts.save("tts.mp3")

        source = discord.FFmpegPCMAudio(
            executable=FFMPEG_PATH,
            source="tts.mp3"
        )

        vc.play(source)

        while vc.is_playing():
            await asyncio.sleep(0.5)

    except Exception as e:
        print("❌ Lỗi TTS:", e)
        await interaction.followup.send(f"❌ Lỗi TTS: {e}")

    finally:
        await vc.disconnect()
        if os.path.exists("tts.mp3"):
            os.remove("tts.mp3")


# ===================== RUN =====================
bot.run(os.environ["DISCORD_TOKEN"])
