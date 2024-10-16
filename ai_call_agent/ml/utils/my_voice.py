import os
import base64
import requests
from io import BytesIO



ELEVEN_LABS_API_KEY = "sk_a6c595d8a81c5a4722ea1247846f54271db6687c784d428c"
VOICE_ID = '21m00Tcm4TlvDq8ikWAM'
OUTPUT_FORMAT = 'ulaw_8000'

def get_audio_from_eleven_labs(text):
    """Calls the Eleven Labs API to convert text to speech."""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {
        'xi-api-key': ELEVEN_LABS_API_KEY,
        'Content-Type': 'application/json'
    }
    payload = {
        'text': text,
        'model_id': 'eleven_turbo_v2',
        'output_format': OUTPUT_FORMAT
    }

    response = requests.post(url, headers=headers, json=payload, stream=True)

    if response.status_code == 200:
        audio_data = BytesIO()
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                audio_data.write(chunk)
        return audio_data.getvalue()

    else:
        print(f"Error from Eleven Labs API: {response.status_code}")
        return None
