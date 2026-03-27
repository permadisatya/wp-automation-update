import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
WEBHOOK_SECRET_TOKEN = os.environ["WEBHOOK_SECRET_TOKEN"]
TELEGRAM_ALLOWLIST = set(map(int, filter(None, os.environ.get("TELEGRAM_ALLOWLIST", "").split(","))))
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
WP_URL = os.environ["WP_URL"].rstrip('/')
WP_USERNAME = os.environ["WP_USERNAME"]
WP_APP_PASSWORD = os.environ["WP_APP_PASSWORD"]

PROMPT_FILE = "system_prompt.txt"
if os.path.exists(PROMPT_FILE):
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        SYSTEM_PROMPT = f.read()
else:
    SYSTEM_PROMPT = "Generate SEO metadata and H5P JSON."

IMAGE_PROMPT_SYSTEM = "You are an expert image prompt engineer. Read the provided text and write a single, highly descriptive prompt for an AI image generator. Focus on visual elements, lighting, style, and subject matter. Output only the final prompt string."