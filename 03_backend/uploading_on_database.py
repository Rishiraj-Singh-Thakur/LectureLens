import os
import ast
import json
import pandas as pd

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


# ---------------------------------------------------------
# Load environment variables
# ---------------------------------------------------------

load_dotenv()


# ---------------------------------------------------------
# Create MySQL Engine
# ---------------------------------------------------------

def get_engine():

    url = URL.create(
        drivername="mysql+pymysql",
        username=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        host=os.getenv("MYSQL_HOST"),
        port=int(os.getenv("MYSQL_PORT")),
        database=os.getenv("MYSQL_DATABASE")
    )

    engine = create_engine(url)

    return engine


# ---------------------------------------------------------
# Upload Existing CSV Data
# ---------------------------------------------------------

def upload_existing_data():

    engine = get_engine()

    csv_path = "01_data/05_embeddings_DF.csv"

    # Load CSV
    df = pd.read_csv(csv_path)

    print(f"CSV loaded: {len(df)} rows")

    # Remove test audio data
    df = df[
        df["lecture_num"] != "test1.mp3"
    ].copy()

    print(
        f"Rows after removing test data: {len(df)}"
    )

    # Convert embedding string into Python list
    df["embedding"] = df["embedding"].apply(
        ast.literal_eval
    )

    # Convert missing lecture titles to None
    # None will become SQL NULL
    df["lecture_title"] = df[
        "lecture_title"
    ].where(
        df["lecture_title"].notna(),
        None
    )

    insert_query = text("""
        INSERT INTO lecture_chunks
        (
            processing_version,
            lecture_num,
            lecture_title,
            start_time,
            end_time,
            text,
            embedding
        )
        VALUES
        (
            :processing_version,
            :lecture_num,
            :lecture_title,
            :start_time,
            :end_time,
            :text,
            :embedding
        )
    """)

    # -----------------------------------------------------
    # Insert into MySQL
    # -----------------------------------------------------

    with engine.begin() as connection:

        for _, row in df.iterrows():

            connection.execute(
                insert_query,
                {
                    "processing_version": 1,

                    "lecture_num": row["lecture_num"],

                    "lecture_title": row["lecture_title"],

                    "start_time": row["start"],

                    "end_time": row["end"],

                    "text": row["text"],

                    # Python list → valid JSON string
                    "embedding": json.dumps(
                        row["embedding"]
                    )
                }
            )

    print(
        f"{len(df)} chunks uploaded successfully!"
    )

# ---------------------------------------------------------
# Save One Processed Lecture To MySQL
# ---------------------------------------------------------

def save_processed_chunks(
    json_path,
    lecture_num,
    lecture_title,
    topic,
    video_id,
    processing_version=1
):
    engine = get_engine()

    with open(json_path, "r", encoding="utf-8") as file:
        content = json.load(file)

    chunks = content["chunks"]

    if not chunks:
        raise ValueError("No chunks found to save.")

    if any("embedding" not in chunk for chunk in chunks):
        raise ValueError("Some chunks are missing embeddings.")

    insert_query = text("""
        INSERT INTO lecture_chunks
        (
            video_id,
            processing_version,
            lecture_num,
            lecture_title,
            topic,
            start_time,
            end_time,
            text,
            embedding
        )
        VALUES
        (
            :video_id,
            :processing_version,
            :lecture_num,
            :lecture_title,
            :topic,
            :start_time,
            :end_time,
            :text,
            :embedding
        )
    """)

    with engine.begin() as connection:
        for chunk in chunks:
            connection.execute(
                insert_query,
                {
                    "video_id": video_id,
                    "processing_version": processing_version,
                    "lecture_num": lecture_num,
                    "lecture_title": lecture_title,
                    "topic": topic,
                    "start_time": chunk["start"],
                    "end_time": chunk["end"],
                    "text": chunk["text"],
                    "embedding": json.dumps(chunk["embedding"])
                }
            )

    print(f"{len(chunks)} chunks saved to MySQL.")
    return len(chunks)
# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

# if __name__ == "__main__":

#     engine = get_engine()

#     # Test MySQL connection
#     with engine.connect():
#         print("MySQL connected successfully")

#     # Upload existing 9 lecture data
#     upload_existing_data()