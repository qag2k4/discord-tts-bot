import discord
from discord.ext import commands
from discord import app_commands
from gtts import gTTS
import os
import shutil  # 👈 THƯ VIỆN CHUẨN, KHÔNG CẦN TẠO FILE RIÊNG

# ================== CẤU HÌNH ==================
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

auto_channels = {}

# ================== HÀM TTS ==================
async def play_tts(voice_client: discord.VoiceClient, text: str):
    file_path = f"/tmp/tts_{voice_client.channel.id}.mp3"

    try:
        # Tạo file mp3
        tts = gTTS(text=text, lang="vi")
        tts.save(file_path)

        if voice_client.is_playing():
            voice_client.stop()

        # 🔍 TÌM ĐÚNG ffmpeg
        ffmpeg_path = shutil.which("ffmpeg")
        print("🔍 ffmpeg path:", ffmpeg_path)

        if ffmpeg_path is None:
            raise RuntimeError("Không tìm thấy ffmpeg trong PATH")

        audio_source = discord.FFmpegPCMAudio(
            source=file_path,
            executable=ffmpeg_path,
            options="-loglevel panic"
        )

        voice_client.play(audio_source)

    except Exception as e:
        print(f"❌ Lỗi TTS runtime: {e}")

# ================== SỰ KIỆN ==================
@bot.event
async def on_ready():
    print(f"✅ Bot đã online: {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Đã đồng bộ {len(synced)} slash command")
    except Exception as e:
        print(f"❌ Lỗi sync slash command: {e}")

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if auto_channels.get(message.channel.id, False):
        if message.author.voice:
            voice_channel = message.author.voice.channel
            voice_client = message.guild.voice_client

            if voice_client is None:
                voice_client = await voice_channel.connect()
            elif voice_client.channel != voice_channel:
                await voice_client.move_to(voice_channel)

            await play_tts(voice_client, message.content)

    await bot.process_commands(message)

# ================== SLASH COMMAND ==================

@bot.tree.command(name="noi", description="Bot đọc nội dung bạn nhập")
@app_commands.describe(text="Nội dung muốn bot đọc")
async def noi(interaction: discord.Interaction, text: str):
    if interaction.user.voice is None:
        await interaction.response.send_message(
            "❌ Bạn phải vào phòng voice trước",
            ephemeral=True
        )
        return

    await interaction.response.defer()

    voice_channel = interaction.user.voice.channel
    voice_client = interaction.guild.voice_client

    if voice_client is None:
        voice_client = await voice_channel.connect()
    elif voice_client.channel != voice_channel:
        await voice_client.move_to(voice_channel)

    await interaction.followup.send(f"🗣️ {text}")
    await play_tts(voice_client, text)

@bot.tree.command(name="auto", description="Bật/tắt tự động đọc tin nhắn")
async def auto(interaction: discord.Interaction):
    channel_id = interaction.channel_id
    auto_channels[channel_id] = not auto_channels.get(channel_id, False)

    if auto_channels[channel_id]:
        await interaction.response.send_message("🔔 Đã bật auto đọc")
    else:
        await interaction.response.send_message("🔕 Đã tắt auto đọc")

@bot.tree.command(name="cut", description="Đuổi bot khỏi phòng voice")
async def cut(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("👋 Bot đã rời phòng voice")
    else:
        await interaction.response.send_message(
            "❌ Bot không ở trong phòng nào",
            ephemeral=True
        )

# ================== RUN ==================
if not TOKEN:
    print("❌ Chưa có TOKEN trong Variables")
else:
    bot.run(TOKEN)
