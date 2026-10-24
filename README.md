# Lecture Timestamp Finder

A web application that helps users find specific topics and their timestamps in Python lecture videos.

## Features
- Search for topics covered in lectures.
- Find relevant lecture timestamps.
- Upload and process lecture videos.
- Transcribe audio using OpenAI Whisper.
- Generate embeddings using Ollama.
- Store and retrieve lecture data using MySQL.

## Tech Stack
- **Backend:** Python, Flask
- **Frontend:** HTML, CSS, JavaScript
- **Database:** MySQL
- **Transcription:** OpenAI Whisper
- **Embeddings:** Ollama (`bge-m3`)
- **Similarity Search:** Scikit-learn

## Requirements
- Python
- MySQL Server
- Ollama with the required models
- FFmpeg

## Setup
1. Clone or download this repository.
2. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Create the MySQL database and configure the environment variables in a `.env` file.
4. Ensure Ollama and FFmpeg are installed and configured.
5. Run the application:

   ```bash
   python app.py
   ```

## Environment Variables
Configure these variables in your local `.env` file:

- `FLASK_SECRET_KEY`
- `MYSQL_HOST`
- `MYSQL_PORT`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_DATABASE`

**Never commit your `.env` file or database credentials to GitHub.**

## Project Status
Currently under development.
