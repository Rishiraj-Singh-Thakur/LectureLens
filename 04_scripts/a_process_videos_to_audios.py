
# Converting Videos to .mp3 using FFMPEG
# -----------------------------------------------------------------------------------------------
import os
import subprocess

# -------------------------------------------------------------------------------------------------
# ============================================================
# Step 1: Convert Uploaded Video To Audio
# ============================================================

def convert_videos_to_audio(video_path, output_path):

    os.makedirs(
        os.path.dirname(output_path),
        exist_ok=True
    )

    result = subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i", video_path,
            "-vn",
            "-acodec", "libmp3lame",
            output_path
        ],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Video-to-audio conversion failed: {result.stderr}"
        )

    return output_path

# ------------------------------------------------------------------------------------------------------

def rename_audio_files():
    audio_dir = "01_data/02_audios"

    audio_files = os.listdir(audio_dir)

    for file in audio_files:
        if file.endswith(".mp4.mp3"):
            new_name = file.replace(".mp4.mp3", ".mp3")

            os.rename(
                os.path.join(audio_dir, file),
                os.path.join(audio_dir, new_name)
            )

            print(f"Renamed: {file} -> {new_name}")
# -------------------------------------------------------------------------------------------------------------
def convert_test_audio():
        input_file = "test1.m4a"
        output_file = "audios/test1.mp3"
        subprocess.run([
                "ffmpeg",
                "-i",
                input_file,
                output_file
        ])

        print("Test audio converted successfully.")

# -----------------------------------------------------------------------------------------------------------------

# ---------------- MAIN ----------------

# convert_videos_to_audio()

# rename_audio_files()

# convert_test_audio()