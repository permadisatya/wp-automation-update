from fastapi import FastAPI, Request, Header, HTTPException
import httpx
from config import TELEGRAM_BOT_TOKEN, WEBHOOK_SECRET_TOKEN, TELEGRAM_ALLOWLIST, WP_URL
import wp_api
import gemini_api
import h5p_processor
import traceback

app = FastAPI()

async def send_telegram_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    async with httpx.AsyncClient() as client:
        await client.post(url, json={"chat_id": chat_id, "text": text})

@app.post("/webhook")
async def telegram_webhook(request: Request, x_telegram_bot_api_secret_token: str = Header(None)):
    if x_telegram_bot_api_secret_token != WEBHOOK_SECRET_TOKEN:
        raise HTTPException(status_code=401)

    update = await request.json()
    message = update.get("message")
    if not message:
        return {"status": "ignored"}

    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    text = message.get("text", "").strip()

    if user_id not in TELEGRAM_ALLOWLIST:
        return {"status": "unauthorized"}

    parts = text.split()
    command = parts[0]

    try:
        if command == "/list":
            drafts = wp_api.get_drafts()
            resp = "\n".join([f"{d['id']}: {d['title']['rendered']}" for d in drafts])
            await send_telegram_message(chat_id, resp or "No drafts found.")

        elif command == "/loadmeta" and len(parts) > 1:
            post = wp_api.get_post(parts[1])
            meta = post.get('yoast_head_json', {})
            await send_telegram_message(chat_id, f"Title: {meta.get('title')}\nDesc: {meta.get('description')}")

        # ... [previous imports and setup] ...

        elif command == "/publish" and len(parts) > 1:
            post_id = parts[1]
            await send_telegram_message(chat_id, f"Initiating automation for {post_id}...")
            
            post = wp_api.get_post(post_id)
            content_html = post.get("content", {}).get("rendered", "")
            
            if not content_html.strip():
                await send_telegram_message(chat_id, "Fatal Error: Empty draft.")
                return {"status": "error"}

            # Fetch Categories Context
            categories_dict = wp_api.get_categories()
            cat_context = "\n".join([f"{k}: {v}" for k, v in categories_dict.items()])

            # AI Text Gen with Category Context
            ai_data = gemini_api.generate_text_payload(content_html, cat_context)
            
            # AI Image Gen Workflow
            paragraphs = [p for p in content_html.split('</p>') if p.strip()]
            img_context = "".join(paragraphs[:2])
            
            # Step 1: Draft Image Prompt
            optimized_image_prompt = gemini_api.draft_image_prompt(img_context)
            
            # Step 2: Generate Image
            webp_bytes = gemini_api.generate_image(optimized_image_prompt)
            
            # WP Uploads
            media_id = wp_api.upload_media(f"header_{post_id}.webp", webp_bytes, "image/webp", ai_data.get("alt_text", "Header"))
            
            h5p_shortcode = ""
            try:
                h5p_bytes = h5p_processor.build_h5p_archive("base_template.h5p", ai_data.get("h5p_data", {}))
                h5p_shortcode = wp_api.upload_h5p(h5p_bytes)
            except Exception as e:
                print(f"H5P Failure: {e}")

            # Construct Post Update
            update_payload = {
                "status": "publish",
                "featured_media": media_id,
                "categories": ai_data.get("categories", []),
                "tags": ai_data.get("tags", []),
                "meta": {
                    "_yoast_wpseo_title": ai_data.get("yoast_wpseo_title", ""),
                    "_yoast_wpseo_metadesc": ai_data.get("yoast_wpseo_metadesc", ""),
                    "_yoast_wpseo_focuskw": ai_data.get("yoast_wpseo_focuskw", "")
                }
            }

            if h5p_shortcode:
                update_payload["content"] = f"{content_html}\n\n{h5p_shortcode}"

            wp_api.update_post(post_id, update_payload)
            await send_telegram_message(chat_id, f"Success. Published: {WP_URL}/?p={post_id}")

# ... [remainder of file] ...

    except Exception as e:
        traceback.print_exc()
        await send_telegram_message(chat_id, f"Fatal Error: {str(e)}")

    return {"status": "ok"}