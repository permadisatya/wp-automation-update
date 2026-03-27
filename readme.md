# WordPress AI Publishing Automation Bot

## Overview
Telegram-triggered automated pipeline for processing unpublished WordPress drafts using the Google Gemini API. Generates SEO metadata, H5P interactive content, and featured images, then publishes the post.

## Configuration
Requires environment variables or a `.env` file containing:
- `TELEGRAM_BOT_TOKEN`: Token from @BotFather.
- `WEBHOOK_SECRET_TOKEN`: Custom 32-character string for webhook security.
- `TELEGRAM_ALLOWLIST`: Comma-separated list of authorized Telegram User IDs.
- `GEMINI_API_KEY`: Google AI Studio API key.
- `WP_URL`: Target WordPress site URL.
- `WP_USERNAME`: WordPress user (Editor role).
- `WP_APP_PASSWORD`: WordPress Application Password.

## Deployment
1. Build container: `docker build -t wp-ai-bot .`
2. Run container: `docker run -d -p 8080:8080 --env-file .env wp-ai-bot`
3. Register webhook: `curl -F "url=https://<YOUR_DOMAIN>/webhook" -F "secret_token=<WEBHOOK_SECRET_TOKEN>" https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/setWebhook`

## Usage
Send commands directly to the configured Telegram bot. Unauthorized users are silently dropped.

### Commands
- `/list`
  Retrieves and outputs a list of all current unpublished WordPress draft IDs and titles.

- `/loadmeta [post_id]`
  Retrieves and outputs the current Yoast SEO metadata for the specified draft ID.

- `/publish [post_id]`
  Initiates the full automation sequence for the specified draft ID. 
  1. Validates draft content.
  2. Generates text metadata and H5P JSON via Gemini.
  3. Generates and converts header image to WEBP via Gemini and Pillow.
  4. Uploads image and sets as featured media.
  5. Compiles and uploads H5P archive.
  6. Updates post with new metadata, inserts H5P shortcode, and changes status to 'publish'.