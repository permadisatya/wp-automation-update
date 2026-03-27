import zipfile
import io
import json
import bleach
from jsonschema import validate, ValidationError

H5P_SCHEMA = {
    "type": "object",
    # Define exact expected schema based on template structure to prevent injection
    "additionalProperties": True 
}

def sanitize_payload(data):
    if isinstance(data, dict):
        return {k: sanitize_payload(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_payload(i) for i in data]
    elif isinstance(data, str):
        return bleach.clean(data, tags=[], attributes={}, strip=True)
    return data

def build_h5p_archive(template_path, json_payload):
    try:
        validate(instance=json_payload, schema=H5P_SCHEMA)
    except ValidationError as e:
        raise ValueError(f"Payload validation failed: {e}")

    clean_payload = sanitize_payload(json_payload)

    with open(template_path, 'rb') as f:
        template_bytes = f.read()

    in_buffer = io.BytesIO(template_bytes)
    out_buffer = io.BytesIO()

    with zipfile.ZipFile(in_buffer, 'r') as zin:
        with zipfile.ZipFile(out_buffer, 'w') as zout:
            for item in zin.infolist():
                if item.filename == 'content/content.json':
                    zout.writestr(item, json.dumps(clean_payload))
                else:
                    zout.writestr(item, zin.read(item.filename))

    return out_buffer.getvalue()