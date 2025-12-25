import discord
from discord.ext import commands
from discord import app_commands
from gtts import gTTS
import os

# ========= TOKEN =========
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    print("❌ Lỗi: Chưa có TOKEN")
    exit(1)

# ========= INTENTS =========
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Lưu trạng thái auto TTS theo channel
auto_channels = {}

# ========= HÀM TTS =========
async def play_tts(voice_client: discord.VoiceClient, text: str):
    file_path = f"tts_{voice_client.channel.id}.mp3"

    try:
        tts = gTTS(text=text, lang="vi")
        tts.save(file_path)

        if voice_client.is_playing():
            voice_client.stop()

        def after_playing(error):
            if os.path.exists(file_path):
                os.remove(file_path)
            if error:
                print(f"❌ Lỗi phát audio: {error}")

        # ⚠️ KHÔNG chỉ định executable -> dùng ffmpeg từ nixpacks
        source = discord.FFmpegPCMAudio(file_path)
        voice_client.play(source, after=after_playing)

    except Exception as e:
        print(f"❌ Lỗi TTS: {e}")

# ========= EVENTS =========
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

    if auto_channels.get(message.channel.id):
        if message.author.voice:
            voice_channel = message.author.voice.channel
            voice_client = message.guild.voice_client

            if voice_client is None:
                voice_client = await voice_channel.connect()
            elif voice_client.channel != voice_channel:
                await voice_client.move_to(voice_channel)

            await play_tts(voice_client, message.content)

    await bot.process_commands(message)

# ========= SLASH COMMANDS =========

@bot.tree.command(name="noi", description="Đọc văn bản thành tiếng")
@app_commands.describe(text="Nội dung muốn đọc")
async def noi(interaction: discord.Interaction, text: str):
    if interaction.user.voice is None:
        await interaction.response.send_message(
            "❌ Bạn chưa vào phòng Voice!",
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

@bot.tree.command(name="auto", description="Bật/Tắt tự động đọc tin nhắn")
async def auto(interaction: discord.Interaction):
    channel_id = interaction.channel_id
    current = auto_channels.get(channel_id, False)

    auto_channels[channel_id] = not current

    if current:
        await interaction.response.send_message(
            "🔕 Đã **TẮT** auto TTS trong kênh này"
        )
    else:
        await interaction.response.send_message(
            "🔔 Đã **BẬT** auto TTS (chat là bot đọc)"
        )

@bot.tree.command(name="cut", description="Đuổi bot khỏi phòng voice")
async def cut(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc:
        await vc.disconnect()
        await interaction.response.send_message("👋 Bye bye!")
    else:
        await interaction.response.send_message(
            "❌ Tôi không ở trong phòng nào",
            ephemeral=True
        )

# ========= RUN =========
bot.run(TOKEN)
