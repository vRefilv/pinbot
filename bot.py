import os
import sqlite3
import discord
from discord.ext import commands
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
PINTEREST_APP_ID = os.getenv('PINTEREST_APP_ID')

# Initialize bot
intents = discord.Intents.default()
bot = commands.Bot(command_prefix='/', intents=intents)

# Database helper functions
DB_FILE = "database.db"

def get_user_token(discord_user_id):
    """Fetch user token from the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT pinterest_token FROM users WHERE discord_id = ?", (discord_user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

# Pinterest API helpers
def get_oauth_url(discord_user_id):
    """Generate Pinterest OAuth URL."""
    redirect_uri = "http://localhost:5000/callback"
    return (f"https://api.pinterest.com/oauth/?response_type=code&client_id={PINTEREST_APP_ID}&redirect_uri={redirect_uri}&"
            f"scope=read_public,write_public&state={discord_user_id}")

def get_pin_image(pin_url, token):
    """Fetch the image URL from a Pinterest pin."""
    pin_id = pin_url.split('/')[-1]
    url = f"https://api.pinterest.com/v1/pins/{pin_id}/"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    return response.json().get("image", {}).get("original", {}).get("url")

# Bot commands
@bot.command(name='login')
async def login(ctx):
    """Send Pinterest login URL to the user."""
    oauth_url = get_oauth_url(ctx.author.id)
    await ctx.author.send(f"Log in to Pinterest here: {oauth_url}")

@bot.command(name='image')
async def fetch_image(ctx, pin_link: str):
    """Fetch and send the image from a Pinterest pin."""
    token = get_user_token(ctx.author.id)
    if not token:
        await ctx.send("Please log in first using `/login`.")
        return

    image_url = get_pin_image(pin_link, token)
    if image_url:
        await ctx.send(image_url)
    else:
        await ctx.send("Could not fetch the image. Check the pin link.")

# Run the bot
bot.run(DISCORD_TOKEN)
