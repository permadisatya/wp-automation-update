import requests
import base64
from config import WP_URL, WP_USERNAME, WP_APP_PASSWORD

credentials = f"{WP_USERNAME}:{WP_APP_PASSWORD}"
encoded_credentials = base64.b64encode(credentials.encode()).decode()

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": USER_AGENT,
    "Authorization": f"Basic {encoded_credentials}"
}

def get_drafts():
    url = f"{WP_URL}/wp-json/wp/v2/posts"
    params = {"status": "draft", "context": "edit", "_fields": "id,title"}
    response = requests.get(url, headers=HEADERS, params=params)
    response.raise_for_status()
    return response.json()

def get_post(post_id):
    url = f"{WP_URL}/wp-json/wp/v2/posts/{post_id}"
    params = {"context": "edit"}
    response = requests.get(url, headers=HEADERS, params=params)
    response.raise_for_status()
    return response.json()

def get_categories():
    url = f"{WP_URL}/wp-json/wp/v2/categories"
    params = {"per_page": 100}
    response = requests.get(url, headers=HEADERS, params=params)
    response.raise_for_status()
    return {c['id']: c['name'] for c in response.json()}

def upload_media(filename, file_bytes, mime_type, alt_text):
    url = f"{WP_URL}/wp-json/wp/v2/media"
    media_headers = {
        "Content-Disposition": f"attachment; filename={filename}",
        "Content-Type": mime_type,
        "User-Agent": USER_AGENT,
        "Authorization": f"Basic {encoded_credentials}"
    }
    response = requests.post(url, headers=media_headers, data=file_bytes)
    response.raise_for_status()
    media_id = response.json().get("id")
    
    update_url = f"{WP_URL}/wp-json/wp/v2/media/{media_id}"
    requests.post(update_url, headers=HEADERS, json={"alt_text": alt_text})
    
    return media_id

def upload_h5p(file_bytes):
    url = f"{WP_URL}/wp-json/h5p/v1/upload"
    h5p_headers = {
        "User-Agent": USER_AGENT,
        "Authorization": f"Basic {encoded_credentials}"
    }
    files = {"file": ("content.h5p", file_bytes, "application/zip")}
    response = requests.post(url, headers=h5p_headers, files=files)
    if response.status_code != 200:
        raise Exception(f"H5P upload failed: {response.status_code} - {response.text}")
    return response.json().get("shortcode")

def update_post(post_id, data):
    url = f"{WP_URL}/wp-json/wp/v2/posts/{post_id}"
    
    # Clean payload: Remove custom fields that aren't native to WP 'posts' endpoint
    # to prevent 400 errors.
    wp_payload = {}
    
    if "categories" in data:
        wp_payload["categories"] = data["categories"]
        
    if "meta" in data:
        wp_payload["meta"] = data["meta"]
    
    # If the post is being published, include status
    wp_payload["status"] = "publish"

    response = requests.post(url, headers=HEADERS, json=wp_payload)
    
    if not response.ok:
        print(f"DEBUG: Rejected Payload: {wp_payload}")
        print(f"DEBUG: WP Message: {response.text}")
        raise Exception(f"WP Update Failed: {response.status_code}")
        
    return response.json()