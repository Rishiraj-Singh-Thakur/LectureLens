import requests
import json
import os


# ============================================================
# Step 4: Create Embeddings Using BGE-M3
# ============================================================

def create_embedding(text_list):

    response = requests.post(
        "http://localhost:11434/api/embed",
        json={
            "model": "bge-m3",
            "input": text_list
        },
        timeout=120
    )

    response.raise_for_status()

    embeddings = response.json().get("embeddings")

    if not embeddings or len(embeddings) != len(text_list):
        raise RuntimeError(
            "Embedding generation failed or returned incomplete results."
        )

    return embeddings


# ============================================================
# Create Embeddings For One Merged JSON File
# ============================================================

def create_embeddings_dataframe(input_json, output_json):

    with open(input_json, "r", encoding="utf-8") as file:
        content = json.load(file)

    chunks = content["chunks"]
    batch_size = 20

    for i in range(0, len(chunks), batch_size):

        batch_chunks = chunks[i:i + batch_size]

        batch_texts = [
            chunk["text"] for chunk in batch_chunks
        ]

        embeddings = create_embedding(batch_texts)

        for chunk, embedding in zip(batch_chunks, embeddings):
            chunk["embedding"] = embedding

        print(
            f"Embeddings created: "
            f"{min(i + batch_size, len(chunks))}/{len(chunks)}"
        )

    os.makedirs(
        os.path.dirname(output_json) or ".",
        exist_ok=True
    )

    with open(output_json, "w", encoding="utf-8") as file:
        json.dump(
            content,
            file,
            indent=4,
            ensure_ascii=False
        )

    print(f"Embeddings saved: {output_json}")

    return output_json