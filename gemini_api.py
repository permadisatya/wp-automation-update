import requests
import base64
import io
import json
from PIL import Image
from config import GEMINI_API_KEY, SYSTEM_PROMPT

def generate_text_payload(content_html, cat_context):
    """Uses Gemini 2.5 Pro for complex structured JSON extraction."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent?key={GEMINI_API_KEY}"
    
    prompt = f"Categories: {cat_context}\n\nContent:\n{content_html}"
    
    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": SYSTEM_PROMPT}]},
            {"role": "user", "parts": [{"text": prompt}]}
        ],
        "generationConfig": {
            "response_mime_type": "application/json"
        }
    }
    
    response = requests.post(url, json=payload)
    if not response.ok:
        raise Exception(f"Gemini Text Error: {response.status_code} - {response.text}")
        
    res_json = response.json()
    text_content = res_json['candidates'][0]['content']['parts'][0]['text']
    return json.loads(text_content)

def generate_image(prompt_text):
    """Uses Gemini 2.5 Flash Image for multimodal output."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt_text}]
        }],
        "generationConfig": {
            "response_modalities": ["IMAGE"]
        }
    }
    
    response = requests.post(url, json=payload)
    if not response.ok:
        raise Exception(f"Gemini Image Error: {response.status_code} - {response.text}")
        
    res_json = response.json()
    parts = res_json.get('candidates', [{}])[0].get('content', {}).get('parts', [])
    image_b64 = next((p['inlineData']['data'] for p in parts if 'inlineData' in p), None)
    
    if not image_b64:
        raise Exception("Model failed to return image data. Check prompt safety filters.")
        
    image_bytes = base64.b64decode(image_b64)
    img = Image.open(io.BytesIO(image_bytes))
    
    if max(img.size) > 1024:
        img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
    
    quality = 90
    while True:
        out_buffer = io.BytesIO()
        img.save(out_buffer, format="WEBP", quality=quality, method=6)
        current_size = out_buffer.tell()
        if current_size <= 1048576 or quality <= 20:
            break
        quality -= 10
        
    return out_buffer.getvalue()

def draft_image_prompt(content_text):
    """
    Reads prompt from prompt_template.txt, injects content_text, and calls Gemini API.
    """
    # Load template
    try:
        with open("prompt_template.txt", "r", encoding="utf-8") as f:
            template = f.read()
    except FileNotFoundError:
        raise FileNotFoundError("prompt_template.txt not found in current directory.")

    # Inject dynamic content
    persona_prompt = template.format(content_text=content_text)

    # API Configuration
    api_key = os.getenv("GEMINI_API_KEY")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [{"text": persona_prompt}]
        }]
    }
    
    response = requests.post(url, json=payload, timeout=30)
    
    if not response.ok:
        raise Exception(f"Prompt Drafting Error: {response.status_code} - {response.text}")
        
    res_json = response.json()
    raw_prompt = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
    
    # Cleaning
    clean_prompt = raw_prompt.replace('`', '').replace('---', '--')
    return clean_prompt