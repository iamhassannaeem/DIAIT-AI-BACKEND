import base64
import json
import os
import tempfile
import wave
import audioop
import soundfile as sf
import numpy as np
import json
import base64
import audioop
import tempfile
import wave
from scipy.io import wavfile
from scipy.signal import resample
from flask import Flask, request, Response
from flask_sock import Sock
import ngrok
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

from twilio_transcriber import TwilioTranscriber
from utils.my_bot import math_tutor
from utils.my_voice import generate_audio


# Flask settings
PORT = 5000
DEBUG = False
INCOMING_CALL_ROUTE = '/'
WEBSOCKET_ROUTE = '/realtime'

# Twilio authentication
account_sid = os.environ['TWILIO_ACCOUNT_SID']
api_key = os.environ['TWILIO_API_KEY_SID']
api_secret = os.environ['TWILIO_API_SECRET']
client = Client(api_key, api_secret, account_sid)
TWILIO_NUMBER = os.environ['TWILIO_NUMBER']

# ngrok authentication
ngrok.set_auth_token(os.getenv("NGROK_AUTHTOKEN"))
app = Flask(__name__)
sock = Sock(app)


def send_raw_audio(ws, file_path, stream_sid):
    try:
        print("Stream SID:", stream_sid)

        # Read the audio file using soundfile
        data, original_samplerate = sf.read(file_path)

        # Convert the data to the required sample rate and mono if necessary
        new_samplerate = 8000
        if len(data.shape) > 1:  # If stereo, take one channel
            data = data[:, 0]

        # Resample the audio to the new sample rate
        duration = data.shape[0] / original_samplerate
        new_length = int(duration * new_samplerate)
        resampled_data = np.interp(np.linspace(0, len(data), new_length), np.arange(len(data)), data)

        # Save the resampled audio to a temporary WAV file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
            temp_filename = temp_wav.name
            sf.write(temp_filename, resampled_data, new_samplerate)

        print("Temporary file created:", temp_filename)

        # Open the temporary WAV file and send the data
        with wave.open(temp_filename, 'rb') as wav_file:
            while True:
                wav_data = wav_file.readframes(320)

                if not wav_data:
                    print("No more data to read.")
                    ws.send(
                        json.dumps({
                            "event": "mark",
                            "streamSid": stream_sid,
                            "mark": {
                                "name": "my label"
                            }
                        })
                    )
                    break

                # Convert linear PCM to mu-law
                mulaw_data = audioop.lin2ulaw(wav_data, 2)

                # Encode to base64
                base64_audio = base64.b64encode(mulaw_data).decode("utf-8")
                ws.send(
                    json.dumps({
                        "event": "media",
                        "streamSid": stream_sid,
                        "media": {
                            "payload": base64_audio
                        }
                    })
                )
    finally:
        print("Finished sending audio.")
        # Optionally remove the temporary file
        # if os.path.exists(temp_filename):
        #     os.remove(temp_filename)


@app.route(INCOMING_CALL_ROUTE, methods=['GET', 'POST'])
def receive_call():
    if request.method == 'POST':
        xml = f"""
<Response>
    <Say>
        Speak to see your speech transcribed in the console
    </Say>
    <Connect>
        <Stream url='wss://{request.host}{WEBSOCKET_ROUTE}' />
    </Connect>
</Response>
""".strip()
        return Response(xml, mimetype='text/xml')
    else:
        return "Real-time phone call transcription app"

def stop_stream(ws,stream_sid):
    ws.send(
    json.dumps({
      "event" : "clear",
      "streamSid": stream_sid,
      })
      )
@sock.route(WEBSOCKET_ROUTE)
def transcription_websocket(ws):
    transcriber = None  # Initialize transcriber outside the loop
    stream_sid = None  # Initialize stream_sid

    while True:
        data = json.loads(ws.receive())
       # print("Received data:", data)  # Log the incoming data for inspection

        match data['event']:
            case "connected":
                transcriber = TwilioTranscriber()
                transcriber.connect()
                # if 'streamSid' in data:  # Check if 'streamSid' exists
                #     #print(f"Connected to stream with SID: {stream_sid}")
                # else:
                #     print("Warning: 'streamSid' not found in connection data.")
            case "start":
                print('Twilio started')
            case "media":
                payload_b64 = data['media']['payload']
                payload_mulaw = base64.b64decode(payload_b64)
                transcriber.stream(payload_mulaw)

                # Get the latest transcript
                transcript_segment = transcriber.get_transcript()

                if transcript_segment:
                    stop_stream(ws,stream_sid)
                    print("from Twilio:", transcript_segment)  # Print the latest transcript segment
                    response = math_tutor(transcript_segment)

                    generate_audio(response)
                    print("from OpenAI:", response)  # Print the response from the math_tutor
                    transcriber.reset_transcript()
                    stream_sid = data['streamSid']  # Capture the stream SID here
                    file_path = "test_voice.wav"  # Replace with your audio file path
                    send_raw_audio(ws,file_path, stream_sid)

            case "stop":
                print('Twilio stopped')
                transcriber.close()
                print('Transcriber closed')


if __name__ == "__main__":
    try:
        # Open Ngrok tunnel

        listener = ngrok.forward(f"http://localhost:{PORT}")
        print(f"Ngrok tunnel opened at {listener.url()} for port {PORT}")
        NGROK_URL = listener.url()

        # Set ngrok URL to be the webhook for the appropriate Twilio number
        twilio_numbers = client.incoming_phone_numbers.list()
        twilio_number_sid = [num.sid for num in twilio_numbers if num.phone_number == TWILIO_NUMBER][0]
        client.incoming_phone_numbers(twilio_number_sid).update(account_sid,
                                                                voice_url=f"{NGROK_URL}{INCOMING_CALL_ROUTE}")

        # run the app
        app.run(port=PORT, debug=DEBUG)
    finally:
        # Always disconnect the ngrok tunnel
        ngrok.disconnect()
