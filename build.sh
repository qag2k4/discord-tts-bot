#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Tải FFmpeg về thư mục ./bin
echo "Downloading FFmpeg..."
mkdir -p bin
curl -L https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz -o ffmpeg.tar.xz
tar -xf ffmpeg.tar.xz
mv ffmpeg-master-latest-linux64-gpl/bin/ffmpeg ./bin/ffmpeg
mv ffmpeg-master-latest-linux64-gpl/bin/ffprobe ./bin/ffprobe
chmod +x ./bin/ffmpeg
chmod +x ./bin/ffprobe

rm -rf ffmpeg-master-latest-linux64-gpl ffmpeg.tar.xz
echo "FFmpeg installed!"
