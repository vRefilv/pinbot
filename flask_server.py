from flask import Flask, request, jsonify
import sqlite3
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
PINTEREST_APP_ID = os.getenv('PINTEREST_APP_ID')
PINTEREST_APP_SECRET = os.getenv('PINTEREST_APP_SECRET')

app = Flask(__name__)
DB_FILE = "database.db"

# Pinterest API helpers
def exchange_code_for_token(code):
    """Exchange authorization code for access token."""
    url = "https://api.pinterest.com/v1/oauth/token"
    data = {
        "grant_type": "authorization_code",
        "client_id": PINTEREST_APP_ID,
        "client_secret": PINTEREST_APP_SECRET,
        "code": code,
    }
    response = requests.post(url, data=data)
    return response.json().get("access_token")

# Database setup
def init_db():
    """Initialize the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discord_id TEXT UNIQUE,
            pinterest_token TEXT
        )
    """)
    conn.commit()
    conn.close()

@app.route('/callback', methods=['GET'])
def oauth_callback():
    """Handle Pinterest OAuth callback."""
    code = request.args.get("code")
    discord_id = request.args.get("state")

    if not code or not discord_id:
        return "Invalid request", 400

    token = exchange_code_for_token(code)
    if not token:
        return "Failed to authenticate with Pinterest", 500

    # Store the token in the database
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (discord_id, pinterest_token)
        VALUES (?, ?)
        ON CONFLICT(discord_id) DO UPDATE SET pinterest_token = excluded.pinterest_token
    """, (discord_id, token))
    conn.commit()
    conn.close()

    return "Authentication successful! You can now use the bot."

if __name__ == "__main__":
    init_db()
    app.run(port=5000)
