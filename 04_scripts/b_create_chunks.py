
# Creating chunks of .mp3's using Whisper ("medium") model

import os
import json
import whisper

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# ============================================================
# Step 2: Transcribe Uploaded Audio And Create Chunks
# ============================================================

def transcribe_audio_files(audio_path, lecture_num, lecture_title, output_json):

    model = whisper.load_model("medium")

    print(f"\nTranscribing: {audio_path}")

    result = model.transcribe(
        audio_path,
        language="hi",
        task="translate",
        word_timestamps=False,
        fp16=False
    )

    chunks = []

    for segment in result["segments"]:
        chunks.append({ 
            "lecture_num": lecture_num,
            "lecture_title": lecture_title,
            "start": round(segment["start"], 2),
            "end": round(segment["end"], 2),
            "text": segment["text"]
        })

    output_data = {
        "lecture_num": lecture_num,
        "lecture_title": lecture_title,
        "full_text": result["text"],
        "chunks": chunks
    }

    os.makedirs(os.path.dirname(output_json), exist_ok=True)

    with open(output_json, "w", encoding="utf-8") as file:
        json.dump(
            output_data,
            file,
            indent=4,
            ensure_ascii=False
        )

    print(f"Transcription completed: {output_json}")

    return output_json
# --------------------------------------------------------------------------------------
# ---------------- MAIN ----------------

# transcribe_audio_files()

