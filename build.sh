#!/usr/bin/env bash
# exit on error
set -o errexit

# 1. Cài đặt các thư viện Python từ requirements.txt
pip install -r requirements.txt

# 2. Tải và cài đặt FFmpeg (Phiên bản Linux)
echo "Downloading FFmpeg..."
mkdir -p bin
curl -L https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz -o ffmpeg.tar.xz
tar -xf ffmpeg.tar.xz
mv ffmpeg-master-latest-linux64-gpl/bin/ffmpeg ./bin/ffmpeg
mv ffmpeg-master-latest-linux64-gpl/bin/ffprobe ./bin/ffprobe
chmod +x ./bin/ffmpeg
chmod +x ./bin/ffprobe

# Dọn dẹp file rác
rm -rf ffmpeg-master-latest-linux64-gpl ffmpeg.tar.xz
echo "FFmpeg installed successfully!"
