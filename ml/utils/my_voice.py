import os
import base64
import requests
from io import BytesIO
from deepgram import DeepgramClient, SpeakOptions


import asyncio
import json
import sys
import websockets
import ssl


from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("ELEVEN_LABS_API_KEY")
dgapi_key = os.getenv("DG_API_KEY")




VOICE_ID = '21m00Tcm4TlvDq8ikWAM'
OUTPUT_FORMAT = 'ulaw_8000'

def get_audio_from_eleven_labs(text):
    """Calls the Eleven Labs API to convert text to speech."""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {
        'xi-api-key': api_key,
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




def get_audio_from_deepGram(text):
    try:
        TEXT = {
             "text": text}


        deepgram = DeepgramClient(dgapi_key)

        options = SpeakOptions(
            model="aura-asteria-en",
            encoding="mulaw",
            sample_rate=8000
        )

        response = deepgram.speak.rest.v("1").stream_raw( TEXT, options)
        response.read()
        # response = response.content  # Skip the first 44 bytes
        return response.content


    except Exception as e:
        print(f"Exception: {e}")

