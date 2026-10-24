import os
import sys
import secrets
import uuid
import webbrowser

from flask_mysqldb import MySQL
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, session, jsonify
# Project paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, "03_backend")
SCRIPTS_DIR = os.path.join(BASE_DIR, "04_scripts")

sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, SCRIPTS_DIR)

from dotenv import load_dotenv

load_dotenv()

# Backend imports
from search_engine import get_answer
from uploading_on_database import save_processed_chunks

# Video processing imports
from a_process_videos_to_audios import convert_videos_to_audio
from b_create_chunks import transcribe_audio_files
from c_merge_chunks import merge_chunks
from d_create_embeddings import create_embeddings_dataframe

app = Flask(
    __name__,
    template_folder="05_templates/templates",
    static_folder="06_static/static"
)

app.secret_key = os.getenv("FLASK_SECRET_KEY")

app.config["MYSQL_HOST"] = os.getenv("MYSQL_HOST")
app.config["MYSQL_PORT"] = int(os.getenv("MYSQL_PORT"))
app.config["MYSQL_USER"] = os.getenv("MYSQL_USER")
app.config["MYSQL_PASSWORD"] = os.getenv("MYSQL_PASSWORD")
app.config["MYSQL_DB"] = os.getenv(
    "MYSQL_DATABASE"
)

mysql = MySQL(app)
# Tracks video upload and processing progress
upload_progress = {}

# ---------------------------------------------------------
# Home Page
# ---------------------------------------------------------
@app.route("/")
def home():
    if "user_id" not in session:
        return redirect("/login")

    cur = mysql.connection.cursor()

    try:
        cur.execute("""
            SELECT video_code, title
            FROM videos
            WHERE video_code IS NOT NULL
            ORDER BY id DESC
        """)
        videos = cur.fetchall()
    finally:
        cur.close()

    return render_template(
        "index.html",
        videos=videos,
        username=session.get("username")
    )

@app.route("/testdb")
def testdb():
    cur = mysql.connection.cursor()
    cur.execute("SELECT DATABASE();")
    result = cur.fetchone()
    cur.close()

    return f"Connected to: {result[0]}"

# @app.route("/users")
# def users():
#     cur = mysql.connection.cursor()

#     cur.execute("SELECT * FROM users")

#     users = cur.fetchall()

#     cur.close()

#     return str(users)

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        cur = mysql.connection.cursor()

        cur.execute(
            "SELECT * FROM users WHERE email = %s AND password = %s",
            (email, password)
        )

        user = cur.fetchone()

        if user:
            session["user_id"] = user[0]
            session["username"] = user[1]
            session["role"] = user[4]

            if user[4] == "admin":
                return redirect("/admin-dashboard")

            else:
                return redirect("/")

        else:
            return """
            Account not found.<br><br>
            <a href='/signup'>Create New Account</a>
            """

    return render_template(
        "auth/login.html"
    )
# ----------
@app.route("/api/upload-progress/<upload_id>")
def get_upload_progress(upload_id):
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    if session.get("role") != "admin":
        return jsonify({"error": "Access Denied"}), 403

    return jsonify(
        upload_progress.get(
            upload_id,
            {"status": "waiting", "step": "Waiting to start", "percent": 0}
        )
    )
# ----------
@app.route("/upload-video", methods=["GET", "POST"])
def upload_video():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        # ---------
        upload_id = request.form.get("upload_id", "").strip()

        if not upload_id:
            return jsonify({"error": "Missing upload ID"}), 400

        upload_progress[upload_id] = {
            "status": "processing",
            "step": "Starting video processing",
            "percent": 0
        }
        # -----------
        video = request.files.get("video")
        if not video or not video.filename:
            return "Please select a video file.", 400

        filename = secure_filename(video.filename)
        if not filename:
            return "Invalid video filename.", 400

        video_code = request.form.get("video_code", "").strip().upper()
        course = request.form.get("course", "").strip()
        lecture_num = request.form.get("lecture_num", "").strip()
        lecture_title = request.form.get("lecture_title", "").strip()
        topic = request.form.get("topic", "").strip()

        if not all([video_code, course, lecture_num, lecture_title, topic]):
            return "All fields are required.", 400

        cur = mysql.connection.cursor()
        try:
            cur.execute(
                "SELECT id FROM videos WHERE video_code = %s",
                (video_code,)
            )
            if cur.fetchone():
                return "Video code already exists. Please use a unique code.", 400
        finally:
            cur.close()

        run_id = str(uuid.uuid4())
        temp_dir = os.path.join("01_data", "processing", run_id)
        os.makedirs(temp_dir, exist_ok=True)
        os.makedirs("uploaded_videos", exist_ok=True)

        name, extension = os.path.splitext(filename)
        stored_filename = f"{name}_{run_id[:8]}{extension}"
        video_path = os.path.join("uploaded_videos", stored_filename)

        try:
            video.save(video_path)
            # -----
            upload_progress[upload_id] = {
                "status": "processing",
                "step": "Saving video to server",
                "percent": 10
            }
            # -----

            cur = mysql.connection.cursor()
            try:
                cur.execute(
                    """
                    INSERT INTO videos
                        (title, file_path, uploaded_by, video_code, status)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        f"{course} - {lecture_title}",
                        video_path,
                        session["user_id"],
                        video_code,
                        "processing"
                    )
                )
                mysql.connection.commit()
                video_id = cur.lastrowid
            finally:
                cur.close()

            audio_path = os.path.join(temp_dir, "audio.mp3")
            # -------
            convert_videos_to_audio(video_path, audio_path)
            upload_progress[upload_id] = {
                "status": "processing",
                "step": "Converting video to audio",
                "percent": 20
            }

            upload_progress[upload_id] = {
                "status": "processing",
                "step": "Transcribing audio with Whisper",
                "percent": 40
            }
            # --------

            old_json = os.path.join(temp_dir, "transcription.json")
            transcribe_audio_files(
                audio_path, lecture_num, lecture_title, old_json
            )

            upload_progress[upload_id] = {
                "status": "processing",
                "step": "Merging transcription chunks",
                "percent": 60
            }
            # ---------

            merged_json = os.path.join(temp_dir, "merged.json")
            # merge_chunks(old_json, merged_json)
            # -------------
            merge_chunks(old_json, merged_json)

            upload_progress[upload_id] = {
                "status": "processing",
                "step": "Generating embeddings",
                "percent": 75
            }
            # -----------------

            embedded_json = os.path.join(temp_dir, "embedded.json")
            # create_embeddings_dataframe(merged_json, embedded_json)
            # --------------
            create_embeddings_dataframe(merged_json, embedded_json)

            upload_progress[upload_id] = {
                "status": "processing",
                "step": "Saving chunks to MySQL database",
                "percent": 90
            }
            # -------------------

            saved_count = save_processed_chunks(
                json_path=embedded_json,
                lecture_num=lecture_num,
                lecture_title=lecture_title,
                topic=topic,
                video_id=video_id,
                processing_version=1
            )
            cur = mysql.connection.cursor()
            try:
                cur.execute(
                    "UPDATE videos SET status = %s WHERE id = %s",
                    ("completed", video_id)
                )
                mysql.connection.commit()
            finally:
                cur.close()
            # ---------------
            upload_progress[upload_id] = {
                "status": "completed",
                "step": "Processing completed successfully!",
                "percent": 100,
                "saved_count": saved_count
            }
            # --------------------

            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

            return (
                f"Lecture processed successfully! "
                f"{saved_count} chunks saved to MySQL. "
                f"Video Code: {video_code}"
            )
        # -----

        except Exception as error:
            upload_progress[upload_id] = {
                "status": "failed",
                "step": "Video processing failed",
                "percent": 0,
                "error": str(error)
            }

            app.logger.exception("Video processing failed")
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

            return (
                "Video uploaded, but processing failed. "
                f"Error: {str(error)}"
            ), 500
        # -------
    return render_template("admin/upload_video.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        cur = mysql.connection.cursor()

        cur.execute(
            """
            INSERT INTO users
            (username, email, password, role)
            VALUES (%s, %s, %s, %s)
            """,
            (username, email, password, "user")
        )

        mysql.connection.commit()

        cur.close()

        return """
            <h2>Account Created Successfully ✅</h2>

            <br>

            <a href='/login'>
                <button>Login Now</button>
            </a>

            <br><br>

            <a href='/'>
                <button>Go To Main Page</button>
            </a>
            """


    return render_template(
        "auth/signup.html"
    )


@app.route("/admin/admin-videos")
def admin_videos():
    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "admin":
        return "Access Denied", 403

    cur = mysql.connection.cursor()

    try:
        cur.execute("""
            SELECT video_code, title
            FROM videos
            WHERE status = 'completed'
            ORDER BY id DESC
        """)
        videos = cur.fetchall()
    finally:
        cur.close()

    return render_template("admin/admin-videos.html", videos=videos)


@app.route("/admin-dashboard")
def admin_dashboard():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Access Denied"

    return render_template(
        "admin/dashboard.html",
        username=session["username"]
    )

# ---------------------------------------------------------
# Lecture Search API
# ---------------------------------------------------------
@app.route("/api/search", methods=["POST"])
def search_lecture():
    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please log in again."
        }), 401

    data = request.get_json(silent=True) or {}
    query = data.get("query", "").strip()
    video_code = data.get("video_code", "").strip().upper()

    if not query or not video_code:
        return jsonify({
            "success": False,
            "message": "Select a lecture and enter a topic."
        }), 400

    cur = mysql.connection.cursor()
    try:
        cur.execute(
            "SELECT id FROM videos WHERE video_code = %s",
            (video_code,)
        )
        video = cur.fetchone()
    finally:
        cur.close()

    if not video:
        return jsonify({
            "success": False,
            "message": "Selected lecture was not found."
        }), 404

    try:
        answer, video_link, lecture_num = get_answer(
            query, video_code
        )

        return jsonify({
            "success": True,
            "answer": answer,
            "video_link": video_link,
            "lecture_num": lecture_num
        })

    except Exception:
        app.logger.exception("Lecture search failed")
        return jsonify({
            "success": False,
            "message": "Search engine failed. Check the Flask terminal."
        }), 500

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")

import webbrowser
if __name__ == "__main__":
    webbrowser.open("http://127.0.0.1:5000")
    app.run(debug=True , use_reloader = False)



# & "C:\Users\Rishiraj singh\anaconda3\python.exe" "c:/Data_Science_journy/Lecture Timestamp Finder (Project -2)/app.py"