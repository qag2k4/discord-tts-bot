# Sử dụng Python 3.10 phiên bản nhẹ (slim)
FROM python:3.10-slim

# Cài đặt FFmpeg và các thư viện cần thiết cho Voice Discord
# Dòng này quan trọng nhất để sửa lỗi bot không nói
RUN apt-get update && \
    apt-get install -y ffmpeg libffi-dev libnacl-dev python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Copy file danh sách thư viện và cài đặt trước (để tối ưu tốc độ build)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ code còn lại (bot.py) vào
COPY . .

# Lệnh chạy bot khi khởi động
CMD ["python", "bot.py"]
