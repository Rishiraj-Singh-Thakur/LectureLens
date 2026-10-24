import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy import text
import json
import numpy as np

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

# ---------------------------------------------------------
# Test Database Connection
# ---------------------------------------------------------

def test_connection():

    engine = get_engine()

    with engine.connect():
        print("MySQL connected successfully")


# ---------------------------------------------------------
# Get Total Chunks
# ---------------------------------------------------------

def get_total_chunks():

    engine = get_engine()

    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT COUNT(*)
                FROM lecture_chunks
            """)
        )

        return result.scalar()


def get_lecture_counts():

    engine = get_engine()

    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT
                    lecture_num,
                    COUNT(*) AS chunk_count
                FROM lecture_chunks
                GROUP BY lecture_num
                ORDER BY lecture_num
            """)
        )

        return result.fetchall()

# ------------------------------------------------------------
# add one chunk
# -------------------------------------------------------------


def get_one_chunk():

    engine = get_engine()

    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT
                    id,
                    lecture_num,
                    lecture_title,
                    start_time,
                    end_time,
                    text,
                    embedding
                FROM lecture_chunks
                LIMIT 1
            """)
        )

        return result.fetchone()

# ----------------------------------------------------------
# get all chunks
# -----------------------------------------------------------
def get_all_chunks():

    engine = get_engine()

    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT
                    id,
                    lecture_num,
                    lecture_title,
                    start_time,
                    end_time,
                    text,
                    embedding
                FROM lecture_chunks
            """)
        )

        return result.fetchall()

# --------------------------------------------------
# get all embeddings
# -----------------------------------------------------
def get_embeddings_array():

    chunks = get_all_chunks()

    embeddings = []

    for chunk in chunks:
        embedding = json.loads(chunk[6])
        embeddings.append(embedding)

    return np.array(embeddings, dtype=np.float32)

# ================================================================
# check video_code column is available or not
# ================================================================
def check_table_columns():
    engine = get_engine()

    with engine.connect() as connection:
        result = connection.execute(text("DESCRIBE videos"))

        for row in result:
            print(row)

# ---------------------------------------------------------
# Check Uploaded Videos
# ---------------------------------------------------------
def check_uploaded_videos():
    try:
        engine = get_engine()

        with engine.connect() as connection:
            result = connection.execute(text("""
                SELECT id, title, file_path
                FROM videos
                ORDER BY id DESC
                LIMIT 10
            """))

            for row in result:
                print(row)

    except Exception as e:
        print("Error:", e)


# ---------------------------------------------------------
# Check Chunks Linked to Video
# ---------------------------------------------------------
def check_video_chunks():
    try:
        engine = get_engine()

        with engine.connect() as connection:
            result = connection.execute(text("""
                SELECT id, video_id, lecture_title, start_time, end_time
                FROM lecture_chunks
                WHERE video_id = 4
            """))

            rows = result.fetchall()

            if rows:
                for row in rows:
                    print(row)
            else:
                print("No chunks found for video_id = 4")

    except Exception as e:
        print("Error:", e)

# ---------------------------------------------------------
# Add Unique Video Code Column
# ---------------------------------------------------------
def add_video_code_column():
    try:
        engine = get_engine()

        with engine.begin() as connection:
            connection.execute(text("""
                ALTER TABLE videos
                ADD COLUMN video_code VARCHAR(50) UNIQUE
            """))

        print("video_code column added successfully.")

    except Exception as e:
        print("Error:", e)

# ---------------------------------------------------------
# Check Existing Video Codes
# ---------------------------------------------------------
def check_existing_video_codes():
    engine = get_engine()

    with engine.connect() as connection:
        result = connection.execute(text("""
            SELECT id, title, video_code
            FROM videos
            ORDER BY id
        """))

        for row in result.fetchall():
            print(row)

# ---------------------------------------------------------
# Assign Video Code
# ---------------------------------------------------------
def assign_video_code():
    engine = get_engine()

    with engine.begin() as connection:
        connection.execute(
            text("""
                UPDATE videos
                SET video_code = :video_code
                WHERE id = :video_id
            """),
            {
                "video_code": "PY101",
                "video_id": 4
            }
        )

    print("Video code PY101 assigned successfully.")

# ---------------------------------------------------------
# Verify Video Code
# ---------------------------------------------------------
def verify_video_code():
    engine = get_engine()

    with engine.connect() as connection:
        result = connection.execute(text("""
            SELECT id, title, video_code
            FROM videos
            WHERE video_code = :video_code
        """), {"video_code": "PY101"})

        for row in result.fetchall():
            print(row)

# ---------------------------------------------------------
# Remove Unique Constraint From Video Code
# ---------------------------------------------------------
def remove_video_code_unique_constraint():

    engine = get_engine()

    with engine.begin() as connection:
        connection.execute(text("""
            ALTER TABLE videos
            DROP INDEX video_code
        """))

    print("Video code uniqueness removed successfully.")


# ---------------------------------------------------------
# Assign Python09 Code To All Videos
# ---------------------------------------------------------
def assign_python09_code():

    engine = get_engine()

    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE videos
                SET video_code = :video_code
            """),
            {"video_code": "Python09"}
        )

        print(f"Videos updated: {result.rowcount}")

# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

if __name__ == "__main__":

    # test_connection()
    # lecture_counts = get_lecture_counts()

    # print("\nLecture-wise Chunks:")

    # for row in lecture_counts:
    #     print(row)

    # total_chunks = get_total_chunks()

    # print("Total Chunks:", total_chunks)
    # print("\nSample Chunk:")

    # sample = get_one_chunk()

    # print(sample)
    # print("\nTotal Chunks From DB:")

    # chunks = get_all_chunks()

    # print("Number of chunks:", len(chunks))
    # embeddings = get_embeddings_array()
    # print("\n Embeddings Array")
    # print(embeddings.shape)
    # check_table_columns()

    # check_uploaded_videos()
    # check_video_chunks()
    # add_video_code_column()
    # check_existing_video_codes()
    # assign_video_code()
    # verify_video_code()
    # remove_video_code_unique_constraint()
    assign_python09_code()





