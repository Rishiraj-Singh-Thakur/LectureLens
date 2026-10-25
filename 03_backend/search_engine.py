import requests
import numpy as np
import re
import os
import json

from dotenv import load_dotenv
from sqlalchemy import create_engine ,text
from sqlalchemy.engine import URL

from lecture_links import lecture_links
from sklearn.metrics.pairwise import cosine_similarity

# ============================================================
# MySQL Database Connection  # search engine
# ============================================================
load_dotenv()

def get_engine():

    url = URL.create(
        drivername="mysql+pymysql",
        username=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        host=os.getenv("MYSQL_HOST"),
        port=int(os.getenv("MYSQL_PORT")),
        database=os.getenv("MYSQL_DATABASE")
    )

    return create_engine(url)
# -------------------------------------------------------------------------------------------------------------------------------------
# ============================================================
# Create Query Embedding Using BGE-M3
# ============================================================

def create_embedding(text_list):

    try:
        response = requests.post(
            "http://localhost:11434/api/embed",
            json={
                "model": "bge-m3",
                "input": text_list
            },
            timeout=120
        )

        response.raise_for_status()

        # Validate Embedding API Response
        embeddings = response.json().get("embeddings")

        if not embeddings:
            raise RuntimeError("Ollama returned an empty embedding response.")

        return embeddings

    except requests.exceptions.RequestException as error:
        print("Ollama Embedding Error:", error)
        return None

# ---------------------------------------------------------
# Load Lecture Chunks From MySQL Using Video Code
# ---------------------------------------------------------
def load_data(video_code):

    engine = get_engine()

    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT
                    lc.id,
                    lc.lecture_num,
                    lc.lecture_title,
                    lc.start_time,
                    lc.end_time,
                    lc.text,
                    lc.embedding
                FROM lecture_chunks AS lc
                INNER JOIN videos AS v
                    ON lc.video_id = v.id
                WHERE v.video_code = :video_code
            """),
            {
                "video_code": video_code.strip().upper()
            }
        )

        rows = result.fetchall()

    data = []

    for row in rows:

        embedding = row[6]

        if isinstance(embedding, str):
            embedding = json.loads(embedding)

        data.append({
            "id": row[0],
            "lecture_num": row[1],
            "lecture_title": row[2],
            "start": row[3],
            "end": row[4],
            "text": row[5],
            "embedding": embedding
        })

    return data

# ----------------------------------------------------------------------------------------------------
# ---------------------------------------------------------
# Load Chunk Vectors For Selected Video And Topic
# ---------------------------------------------------------
def load_chunk_vectors(video_code):

    data = load_data(video_code)

    if not data:
        return data, np.empty((0, 0), dtype=np.float32)

    chunk_vectors = np.array(
        [chunk["embedding"] for chunk in data],
        dtype=np.float32
    )

    return data, chunk_vectors
# ---------------------------------------------------------
# Retrieve Top Chunks For Selected Video And Topic
# ---------------------------------------------------------
def search(query, video_code):

    data, chunk_vectors = load_chunk_vectors(
        video_code,
    )

    if not data:
        return [], np.array([])

    query_embedding = create_embedding([query])

    if not query_embedding:
        raise RuntimeError(
            "Could not create query embedding. Check whether Ollama is running."
        )

    query_vector = np.array(
        query_embedding[0],
        dtype=np.float32
    ).reshape(1, -1)

    # Calculate Cosine Similarity
    scores = cosine_similarity(
        query_vector,
        chunk_vectors
    )[0]

    # Retrieve Top 2 Chunks
    top_indices = scores.argsort()[-2:][::-1]

    top_scores = scores[top_indices]

    retrieved_chunks = [
        data[index]
        for index in top_indices
    ]

    return retrieved_chunks, top_scores

# ---------------------------------------------------------------------------------------------------------------
# converting time in min:sec

def seconds_to_timestamp(seconds):

    hours = int(seconds // 3600)

    minutes = int((seconds % 3600) // 60)

    seconds = int(seconds % 60)

    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

# ============================================================
# Build Context For LLM
# ============================================================

def build_context(retrieved_chunks):

    context_lines = []

    for chunk in retrieved_chunks:

        timestamp = seconds_to_timestamp(
            chunk["start"]
        )

        context_lines.append(
            f"Lecture: {chunk['lecture_num']}\n"
            f"Title: {chunk['lecture_title']}\n"
            f"Timestamp: {timestamp}\n"
            f"Text: {chunk['text']}"
        )

    return "\n\n".join(context_lines)

# ----------------------------------------------------------------------------------------------------------------------------

# Build Prompt
def build_prompt(query, context):
    prompt = f"""
You are a Lecture Timestamp Assistant.

Your job is to help students find where a topic is taught in lecture videos from a Python course.

User Question:
{query}

Retrieved Lecture Chunks:
{context}

Instructions:
# 1. Use the retrieved chunks to identify the most relevant lecture and timestamp.
# 2. Use the lecture title, retrieved text, and your general Python knowledge to explain the topic in a beginner-friendly way.
# 3. Do not invent lecture names, timestamps, or retrieved content.
# 4. Identify the most relevant lecture.
# 5. Mention the timestamp of the most relevant chunk.
# 6. If the topic is not present in the retrieved chunks, reply:
#     "I could not find this topic in the available lectures."
# 7. Keep the response concise and student-friendly.
# 8. Use the lecture title exactly as provided in the retrieved chunks.
# 9. Do not explain why the chunk was selected.
# 10. Do not mention relevance scores, semantic matches, retrieval, chunks, embeddings, or search process.
# 11. Focus on helping the student learn the topic.
# 12. Explain the topic in 2–3 simple sentences suitable for beginners.
# 13. Always include both the lecture number and lecture title.
# 14. Use the retrieved chunks only for selecting the lecture and timestamp.
# 15. Use your general Python knowledge only for explaining the topic.
# 16. Keep response under 100 words.
Output Format:
📚 Lecture:
<lecture title> - <lecture number>

⏱ Timestamp:
<mm:ss>

🎯 Start Watching From:
<timestamp>

📝 What You'll Learn:
<short student-friendly explanation>"""
    return prompt

# ---------------------------------------------------------------------------------------------------------
# '''                                       Open Ai Code                 '''

# OpenAI Code (optional)

# from openai import OpenAI
# import os

# client = OpenAI(
#     api_key=os.getenv("OPENAI_API_KEY")
# )

# def generate_answer(prompt):
#     response = client.responses.create(
#         model="gpt-5",
#         input=prompt
#     )
#     return response.output_text

# --------------------------------------------------------------------------------------------------------------------------------------------------------------

# ------------------------------------------------------------------------------------------------------------------------------
# '''                               Ollama Model Code                   '''

# Give prompt to Ollama model (ollama pull qwen2.5:7b) and take output_text by model

# Dounload ollama qwen2.5:7b  (model 4.7GB)
# ============================================================
# Generate Answer Using Groq API
# ============================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


def llm_output(prompt):

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.2
            },
            timeout=120
        )

        response.raise_for_status()

        answer = response.json()["choices"][0]["message"]["content"]

        if not answer:
            raise RuntimeError("Groq returned an empty answer.")

        return answer

    except requests.exceptions.RequestException as error:
        raise RuntimeError(
            f"Groq answer generation failed: {error}"
        ) from error

# ---------------------------------------------------------
# Get Answer For Selected Video And Topic
# ---------------------------------------------------------
def get_answer(query, video_code):

    retrieved_Top_chunks, top_scores = search(
        query,
        video_code,
    )

    if not retrieved_Top_chunks:
        return (
            "I could not find this topic in the selected video.",
            "#",
            None
        )

    context = build_context(
        retrieved_Top_chunks
    )

    prompt = build_prompt(
        query,
        context
    )

    answer = llm_output(prompt)

    match = re.search(
        r"Lecture-\d+",
        answer
    )

    if match:
        top_lecture = match.group()
    else:
        top_lecture = retrieved_Top_chunks[0]["lecture_num"]

    video_link = lecture_links.get(
        top_lecture,
        "#"
    )

    return answer, video_link, top_lecture

# ============================================================
# Run Search Engine
# ============================================================

if __name__ == "__main__":

    video_code = input("Enter Video Code: ").strip().upper()
    query = input("Ask Question: ").strip()

    answer, video_link, top_lecture = get_answer(
        query,
        video_code,
    )

    print("\nAnswer:")
    print(answer)

    print("\nVideo Link:")
    print(video_link)

    print("\nLecture Number:")
    print(top_lecture)