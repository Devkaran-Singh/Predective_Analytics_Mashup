import os
import sys
import shutil
import subprocess
import imageio_ffmpeg as ffmpeg
from yt_dlp import YoutubeDL

# Parsing Arguments
if len(sys.argv) != 5:
    print("Usage:")
    print("python program.py <SingerName> <NumberOfVideos(10 or more)> <AudioDuration(20 or more)> <OutputFileName>")
    sys.exit(1)

SINGER_NAME = sys.argv[1]
N = int(sys.argv[2])       
Y = int(sys.argv[3])          
FINAL_OUTPUT = sys.argv[4]

if N < 10:
    print("Number of videos must be at least 10.")
    sys.exit(1)

if Y < 20:
    print("Audio duration must be at least 20 seconds.")
    sys.exit(1)

DOWNLOAD_DIR = "downloads"
AUDIO_DIR = "audio"
CUT_DIR = "cut_audio"

os.makedirs(DOWNLOAD_DIR, exist_ok = True)
os.makedirs(AUDIO_DIR, exist_ok = True)
os.makedirs(CUT_DIR, exist_ok = True)
FFMPEG_PATH = ffmpeg.get_ffmpeg_exe()

def clean_workspace():
    for folder in ["downloads", "audio", "cut_audio"]:
        if os.path.exists(folder):
            shutil.rmtree(folder)
    if os.path.exists(FINAL_OUTPUT):
        os.remove(FINAL_OUTPUT)

# Downloading Videos
def download_videos(singer, n):
    search_query = f"ytsearch{n}:{singer} songs"
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": f"{DOWNLOAD_DIR}/%(title)s.%(ext)s",
        "quiet": True
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([search_query])

# Converting videos to audios
def convert_to_audio():
    for file in os.listdir(DOWNLOAD_DIR):
        input_path = os.path.join(DOWNLOAD_DIR, file)
        output_path = os.path.join(
            AUDIO_DIR, os.path.splitext(file)[0] + ".mp3"
        )
        subprocess.run(
            [FFMPEG_PATH, "-y", "-i", input_path, "-vn", "-ab", "192k", output_path],
            stdout = subprocess.DEVNULL,
            stderr = subprocess.DEVNULL
        )

# Cutting audio to Y seconds
def cut_audio():
    for file in os.listdir(AUDIO_DIR):
        input_path = os.path.join(AUDIO_DIR, file)
        output_path = os.path.join(CUT_DIR, file)
        subprocess.run([
            FFMPEG_PATH, "-y", "-i", input_path,
            "-t", str(Y),
            output_path
        ], stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)

# Merging all audios
def merge_audio(final_output):
    list_file = "files.txt"
    with open(list_file, "w", encoding = "utf-8") as f:
        for file in sorted(os.listdir(CUT_DIR)):
            f.write(f"file '{os.path.join(CUT_DIR, file)}'\n")
    subprocess.run([
        FFMPEG_PATH, "-y", "-f", "concat", "-safe", "0",
        "-i", list_file,
        "-c", "copy",
        final_output
    ], stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
    os.remove(list_file)

def main():
    clean_workspace()
    os.makedirs(DOWNLOAD_DIR, exist_ok = True)
    os.makedirs(AUDIO_DIR, exist_ok = True)
    os.makedirs(CUT_DIR, exist_ok = True)
    print(f"Singer       : {SINGER_NAME}")
    print(f"Videos       : {N}")
    print(f"Duration     : {Y} seconds")
    print(f"Output File  : {FINAL_OUTPUT}")
    download_videos(SINGER_NAME, N)
    convert_to_audio()
    cut_audio()
    merge_audio(FINAL_OUTPUT)
    print(f"Final merged file saved as: {FINAL_OUTPUT}")

if __name__ == "__main__":
    main()
