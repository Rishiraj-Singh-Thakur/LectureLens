import os
import json
import math

chunks_size = 3


# ============================================================
# Step 3: Merge Transcription Chunks
# ============================================================

def merge_chunks(input_json, output_json):

    with open(input_json, "r", encoding="utf-8") as file:
        data = json.load(file)

    old_chunks = data["chunks"]
    new_chunks = []

    num_chunks = len(old_chunks)
    num_groups = math.ceil(num_chunks / chunks_size)

    for i in range(num_groups):
        start_idx = i * chunks_size
        end_idx = min((i + 1) * chunks_size, num_chunks)

        chunk_group = old_chunks[start_idx:end_idx]

        new_chunks.append({
            "lecture_num": data["lecture_num"],
            "lecture_title": data["lecture_title"],
            "start": chunk_group[0]["start"],
            "end": chunk_group[-1]["end"],
            "text": " ".join(
                chunk["text"] for chunk in chunk_group
            )
        })

    os.makedirs(
        os.path.dirname(output_json) or ".",
        exist_ok=True
    )

    with open(output_json, "w", encoding="utf-8") as file:
        json.dump(
            {
                "lecture_num": data["lecture_num"],
                "lecture_title": data["lecture_title"],
                "full_text": data["full_text"],
                "chunks": new_chunks
            },
            file,
            indent=4,
            ensure_ascii=False
        )

    print(f"Merged chunks saved: {output_json}")

    return output_json