import discord
from discord.ext import commands
from discord import app_commands
from gtts import gTTS
import os
import asyncio
from keep_alive import keep_alive  # Import server để giữ bot sống trên Render

# --- CẤU HÌNH BOT ---
TOKEN = os.getenv("TOKEN")

# Bật tất cả quyền cần thiết
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Biến lưu trạng thái kênh nào đang bật Auto
auto_channels = {} 

# --- HÀM XỬ LÝ TTS (Dùng chung cho cả lệnh và Auto) ---
async def play_tts(voice_client, text, ctx_or_interaction):
    # Xác định FFmpeg cho Render
    if os.path.exists("./bin/ffmpeg"):
        ffmpeg_executable = "./bin/ffmpeg"
    else:
        ffmpeg_executable = "ffmpeg"

    file_path = f"tts_{voice_client.channel.id}.mp3"

    try:
        # Tạo file âm thanh
        tts = gTTS(text=text, lang="vi")
        tts.save(file_path)

        # Nếu đang nói dở thì dừng để nói câu mới (hoặc bạn có thể code thêm hàng chờ nếu muốn)
        if voice_client.is_playing():
            voice_client.stop()

        # Hàm xóa file sau khi đọc xong
        def after_playing(error):
            if os.path.exists(file_path):
                os.remove(file_path)
            if error:
                print(f"Lỗi playback: {error}")

        source = discord.FFmpegPCMAudio(file_path, executable=ffmpeg_executable)
        voice_client.play(source, after=after_playing)
    
    except Exception as e:
        print(f"Lỗi TTS: {e}")
        # Gửi thông báo lỗi (kiểm tra xem là ctx hay interaction để gửi đúng cách)
        msg = f"❌ Lỗi: {e}"
        if isinstance(ctx_or_interaction, discord.Interaction):
            await ctx_or_interaction.followup.send(msg, ephemeral=True)
        else:
            await ctx_or_interaction.send(msg)

# --- SỰ KIỆN KHI BOT ONLINE ---
@bot.event
async def on_ready():
    print(f"✅ Bot đã online: {bot.user}")
    try:
        # ĐỒNG BỘ LỆNH SLASH (QUAN TRỌNG ĐỂ HIỆN DẤU /)
        synced = await bot.tree.sync()
        print(f"✅ Đã đồng bộ {len(synced)} lệnh Slash Command.")
    except Exception as e:
        print(f"❌ Lỗi đồng bộ lệnh: {e}")

# --- SỰ KIỆN TỰ ĐỘNG ĐỌC TIN NHẮN (AUTO) ---
@bot.event
async def on_message(message):
    # Không để bot tự đọc tin nhắn của chính nó hoặc bot khác
    if message.author.bot:
        return

    # Kiểm tra xem kênh này có đang bật Auto không
    if message.channel.id in auto_channels and auto_channels[message.channel.id] is True:
        if message.author.voice: # Chỉ đọc nếu người chat đang ở trong voice
            voice_channel = message.author.voice.channel
            voice_client = message.guild.voice_client

            # Nếu bot chưa vào, hoặc đang ở phòng khác -> Kéo bot về
            if voice_client is None:
                voice_client = await voice_channel.connect()
            elif voice_client.channel != voice_channel:
                await voice_client.move_to(voice_channel)
            
            # Đọc nội dung tin nhắn
            await play_tts(voice_client, message.content, message.channel)

    # Dòng này để bot vẫn hiểu lệnh prefix cũ (!) nếu cần
    await bot.process_commands(message)

# ================= CÁC LỆNH SLASH COMMAND (DÙNG /) =================

# 1. Lệnh nói thủ công: /noi [nội dung]
@bot.tree.command(name="noi", description="Đọc văn bản thành tiếng (Chị Google)")
@app_commands.describe(text="Nội dung muốn nói")
async def noi(interaction: discord.Interaction, text: str):
    if interaction.user.voice is None:
        await interaction.response.send_message("❌ Bạn chưa vào phòng Voice!", ephemeral=True)
        return

    await interaction.response.defer() # Báo cho Discord biết bot đang xử lý (tránh lỗi 'The application did not respond')
    
    voice_channel = interaction.user.voice.channel
    voice_client = interaction.guild.voice_client

    if voice_client is None:
        voice_client = await voice_channel.connect()
    elif voice_client.channel != voice_channel:
        await voice_client.move_to(voice_channel)

    await interaction.followup.send(f"🗣️ **{interaction.user.name}** nói: {text}")
    await play_tts(voice_client, text, interaction)

# 2. Lệnh bật chế độ tự động: /auto
@bot.tree.command(name="auto", description="Bật/Tắt chế độ tự động đọc tin nhắn trong kênh này")
async def auto(interaction: discord.Interaction):
    channel_id = interaction.channel_id
    current_status = auto_channels.get(channel_id, False)
    
    if current_status:
        auto_channels[channel_id] = False
        await interaction.response.send_message("🔕 Đã **TẮT** chế độ tự động đọc tại kênh này.")
    else:
        auto_channels[channel_id] = True
        await interaction.response.send_message("🔔 Đã **BẬT** chế độ tự động đọc! (Chỉ cần chat, bot sẽ tự nói).")

# 3. Lệnh đuổi bot: /cut
@bot.tree.command(name="cut", description="Đuổi bot ra khỏi phòng Voice")
async def cut(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("👋 Bye bye!", ephemeral=False)
    else:
        await interaction.response.send_message("❌ Tôi có đang ở trong phòng nào đâu?", ephemeral=True)

# --- WEB SERVER ---
keep_alive()

# --- CHẠY BOT ---
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ Lỗi: Chưa có TOKEN")
