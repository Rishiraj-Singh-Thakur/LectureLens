from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

API_KEY = os.environ["OLLAMA_PROXY_KEY"]
OLLAMA_URL = "http://localhost:11434"

@app.before_request
def authenticate():
    if request.headers.get("X-API-Key") != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401

@app.route("/api/<path:endpoint>", methods=["GET", "POST"])
def ollama_api(endpoint):
    response = requests.request(
        method=request.method,
        url=f"{OLLAMA_URL}/api/{endpoint}",
        json=request.get_json(silent=True),
        timeout=300
    )
    return (response.content, response.status_code,
            {"Content-Type": response.headers.get("Content-Type", "application/json")})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)